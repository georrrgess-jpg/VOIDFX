"""Source restoration: Real-ESRGAN compact (SRVGGNetCompact, realesr-general-x4v3) for the 720p packs.

The network is re-implemented here; the official release weights are loaded tensors-only (weights_only=True) and
blended with the denoising (wdn) weights as Real-ESRGAN does (dn = how much of the plain model). It is exported once
to ONNX and run with ONNX Runtime (about 1.7x faster than torch on CPU).

  v3/models/realesr-general-x4v3.pth, realesr-general-wdn-x4v3.pth   (github.com/xinntao/Real-ESRGAN, release v0.2.5.0)
  v3/models/sr_dn05.onnx                                              (exported by onnx_session() on first use)
"""
import os, numpy as np, cv2

MDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v3", "models")


def _net(dn=0.5):
    import torch, torch.nn as nn, torch.nn.functional as F

    class SRVGGNetCompact(nn.Module):
        def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
            super().__init__(); self.upscale = upscale
            self.body = nn.ModuleList([nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)])
            for _ in range(num_conv):
                self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1)); self.body.append(nn.PReLU(num_parameters=num_feat))
            self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
            self.upsampler = nn.PixelShuffle(upscale)

        def forward(self, x):
            out = x
            for l in self.body: out = l(out)
            return self.upsampler(out) + F.interpolate(x, scale_factor=self.upscale, mode="nearest")

    def w(p):
        d = torch.load(p, map_location="cpu", weights_only=True)            # tensors only: no pickled code runs
        return d.get("params", d)
    a = w(f"{MDIR}/realesr-general-x4v3.pth"); b = w(f"{MDIR}/realesr-general-wdn-x4v3.pth")
    net = SRVGGNetCompact(); net.load_state_dict({k: dn * a[k] + (1 - dn) * b[k] for k in a}, strict=True); net.eval()
    return net


def onnx_session(threads=4, dn=0.5):
    import onnxruntime as ort
    path = f"{MDIR}/sr_dn{int(dn * 10):02d}.onnx"
    if not os.path.exists(path):
        import torch
        torch.onnx.export(_net(dn), torch.rand(1, 3, 720, 440), path, input_names=["x"], output_names=["y"], opset_version=17,
                          dynamic_axes={"x": {2: "h", 3: "w"}, "y": {2: "h4", 3: "w4"}}, dynamo=False)
    so = ort.SessionOptions(); so.intra_op_num_threads = threads
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])


def sr2(sess, bgr):
    """BGR uint8 -> 2x BGR uint8 (the 4x network output, area-downsampled to 2x: cleaner than the raw 4x)."""
    x = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255
    y = np.clip(sess.run(None, {"x": np.ascontiguousarray(x)})[0][0].transpose(1, 2, 0), 0, 1)
    h, w = bgr.shape[:2]
    y = cv2.resize(y, (2 * w, 2 * h), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor((y * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR)
