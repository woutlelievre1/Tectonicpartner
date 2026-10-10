import numpy as np, soundfile as sf, json, pyloudnorm as pyln, sys
W=sys.argv[1] if len(sys.argv)>1 else "work"
T=json.load(open(f"{W}/timeline.json")); o={int(k):v for k,v in T["out"].items()}; vo=T["vo"]
m,sr=sf.read(f"{W}/master.wav"); V,_=sf.read(f"{W}/stem_vo.wav"); Mu,_=sf.read(f"{W}/stem_music.wav")
met=pyln.Meter(sr)
print("integrated master %.2f LUFS  sample peak %.2f dBFS"%(met.integrated_loudness(m),20*np.log10(abs(m).max())))
def lufs(x,a,b):
    seg=x[int(a*sr):int(b*sr)]
    return met.integrated_loudness(seg) if len(seg)>sr*0.4 else float('nan')
phr=[("Every great movement…spark",vo["spark"]-2.62,vo["spark"]+0.5),("An idea…today",vo["spark"]+0.9,vo["people"]-2.9),("But ideas…world",vo["people"]-2.7,vo["people"]-0.1),
("People do. The dreamers…",vo["people"],vo["people"]+6),("Behind every…did",vo["you"]-5,vo["you"]-0.9),("You are one of them",vo["you"],vo["you"]+1.3),
("This October…together",vo["this"],vo["this"]+2.6),("one generation…built",vo["this"]+2.8,vo["toour"]-0.7),("To our partners…building",vo["toour"],vo["future"]-0.9),
("The future is calling",vo["future"],vo["future"]+1.45),("October 21…Ghent",vo["future"]+2.0,vo["ghent"]+0.45),("Welcome (word)",vo["ghent"]+1.66,vo["ghent"]+2.25),("…to (swell)",vo["ghent"]+2.25,vo["tec"]),
("TECTONIC",vo["tec"],vo["tec"]+0.75),("Together we shape what's next",vo["together"],vo["next_end"])]
print(f"{'phrase':34s} VO LUFS  MUS LUFS  VO-MUS")
for n,a,b in phr:
    lv,lm=lufs(V,a,b),lufs(Mu,a,b); print(f"{n:34s} {lv:7.1f} {lm:8.1f} {lv-lm:7.1f}")
# short-term loudness every 1 s (3 s window)
st=[]
for t in np.arange(1.5,len(m)/sr-1.5,1.0):
    st.append((t,lufs(m,t-1.5,t+1.5)))
print("short-term master:"," ".join(f"{t:.0f}:{v:.0f}" for t,v in st))
