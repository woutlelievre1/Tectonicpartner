import sherpa_onnx, soundfile as sf, json
d="models/sherpa-onnx-zipformer-en-2023-06-26/"
r=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d+"encoder-epoch-99-avg-1.onnx",decoder=d+"decoder-epoch-99-avg-1.onnx",joiner=d+"joiner-epoch-99-avg-1.onnx",tokens=d+"tokens.txt",decoding_method="modified_beam_search")
x,sr=sf.read("work/vo16.wav",dtype="float32")
s=r.create_stream(); s.accept_waveform(sr,x); r.decode_stream(s)
res=s.result
print(repr(res.tokens[:6]))
# group tokens into words
words=[];cur=None
for t,ts in zip(res.tokens,res.timestamps):
    if t.startswith(" ") or t.startswith("▁") or cur is None:
        if cur: words.append(cur)
        cur=[t.strip().lstrip("▁"),ts]
    else: cur[0]+=t
if cur: words.append(cur)
json.dump(words,open("words.json","w"))
print(" ".join(f"{w}@{t:.2f}" for w,t in words))
