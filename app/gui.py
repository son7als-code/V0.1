from __future__ import annotations
import tempfile, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from .media import ffprobe, extract_frames
from .ocr_engine import ocr_image, build_cues
from .translator import VietnameseTranslator
from .tts_engine import synthesize
from .render import render
from .dictionary import ProperNameDictionary, OCRMemory, OCRCorrection
from .correction import OCRCorrector

ROOT=Path(__file__).resolve().parents[1]

class VietDubApp(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('VietDub AI - Chinese → Vietnamese'); self.geometry('1120x740'); self.minsize(900,620)
        self.video=None; self.info={}; self.region=None; self.cues=[]; self.work=None; self._build()
    def _build(self):
        s=ttk.Style(self); s.configure('Title.TLabel',font=('Segoe UI',20,'bold')); s.configure('Step.TLabel',font=('Segoe UI',11,'bold'))
        top=ttk.Frame(self,padding=12); top.pack(fill='x'); ttk.Label(top,text='VIETDUB AI',style='Title.TLabel').pack(side='left'); ttk.Button(top,text='🎬 Chọn video MP4',command=self.choose_video).pack(side='right')
        self.video_label=ttk.Label(self,text='Chưa chọn video',padding=10); self.video_label.pack(fill='x')
        nb=ttk.Notebook(self); nb.pack(fill='both',expand=True,padx=12,pady=8)
        self.tabs=[]
        for name in ['1. VIDEO','2. VÙNG OCR','3. OCR / DỊCH','4. TTS / XUẤT','5. TÊN RIÊNG','6. OCR MEMORY']:
            t=ttk.Frame(nb,padding=12); nb.add(t,text=name); self.tabs.append(t)
        self._video_tab(self.tabs[0]); self._ocr_tab(self.tabs[1]); self._edit_tab(self.tabs[2]); self._run_tab(self.tabs[3]); self._dict_tab(self.tabs[4]); self._mem_tab(self.tabs[5])
        self.log=tk.Text(self,height=7); self.log.pack(fill='x',padx=12,pady=(0,12)); self.log.configure(state='disabled')
    def logmsg(self,s):
        self.log.configure(state='normal'); self.log.insert('end',s+'\n'); self.log.see('end'); self.log.configure(state='disabled')
    def _video_tab(self,t):
        ttk.Label(t,text='VIDEO NGUỒN',style='Step.TLabel').pack(anchor='w'); self.video_info=ttk.Label(t,text='Chọn video để bắt đầu.'); self.video_info.pack(anchor='w',pady=10); ttk.Button(t,text='Chọn video từ máy tính',command=self.choose_video).pack(anchor='w')
    def _ocr_tab(self,t):
        ttk.Label(t,text='VÙNG PHỤ ĐỀ',style='Step.TLabel').pack(anchor='w'); ttk.Label(t,text='X/Y/W/H là tỷ lệ 0..1 theo khung hình. Mặc định vùng phụ đề phía dưới.').pack(anchor='w',pady=5)
        f=ttk.Frame(t); f.pack(anchor='w',pady=8); self.vars={k:tk.StringVar(value=v) for k,v in {'x':'0.05','y':'0.75','w':'0.90','h':'0.20','fps':'1'}.items()}
        for k in ['x','y','w','h','fps']: ttk.Label(f,text=k.upper()).pack(side='left'); ttk.Entry(f,textvariable=self.vars[k],width=7).pack(side='left',padx=(3,12))
        ttk.Button(t,text='🔎 CHẠY OCR',command=self.start_ocr).pack(anchor='w',pady=10)
    def _edit_tab(self,t):
        ttk.Label(t,text='OCR / DỊCH',style='Step.TLabel').pack(anchor='w')
        cols=('id','start','end','ocr','vi','conf'); self.tree=ttk.Treeview(t,columns=cols,show='headings',height=17)
        heads={'id':'#','start':'Bắt đầu','end':'Kết thúc','ocr':'Tiếng Trung','vi':'Tiếng Việt','conf':'OCR'}
        for c in cols: self.tree.heading(c,text=heads[c]); self.tree.column(c,width=70 if c not in ('ocr','vi') else 300)
        self.tree.pack(fill='both',expand=True); self.tree.bind('<Double-1>',self.edit_selected)
        b=ttk.Frame(t); b.pack(fill='x',pady=8); ttk.Button(b,text='✏ Sửa câu chọn',command=self.edit_selected).pack(side='left'); ttk.Button(b,text='🌐 Dịch tất cả',command=self.translate_all).pack(side='left',padx=8); ttk.Button(b,text='💾 Lưu OCR Memory',command=self.save_corrections).pack(side='left')
        ttk.Label(t,text='Có thể double-click một dòng để sửa OCR tiếng Trung hoặc tiếng Việt.').pack(anchor='w')
    def _run_tab(self,t):
        ttk.Label(t,text='TTS / XUẤT VIDEO',style='Step.TLabel').pack(anchor='w'); f=ttk.Frame(t); f.pack(anchor='w',pady=10)
        ttk.Label(f,text='Giọng:').pack(side='left'); self.voice=tk.StringVar(value='vi-VN-HoaiMyNeural'); ttk.Combobox(f,textvariable=self.voice,values=['vi-VN-HoaiMyNeural','vi-VN-NamMinhNeural'],width=27).pack(side='left',padx=8)
        ttk.Label(f,text='Xuất:').pack(side='left'); self.res=tk.StringVar(value='1080p'); ttk.Combobox(f,textvariable=self.res,values=['720p','1080p','2K'],state='readonly',width=10).pack(side='left',padx=8)
        ttk.Button(t,text='🚀 TẠO TTS + XUẤT MP4',command=self.start_render).pack(anchor='w',pady=12); self.progress=ttk.Progressbar(t,maximum=100); self.progress.pack(fill='x'); self.status=ttk.Label(t,text='Sẵn sàng'); self.status.pack(anchor='w',pady=6)
    def _dict_tab(self,t):
        ttk.Label(t,text='BẢNG TÊN RIÊNG — LƯU LÂU DÀI',style='Step.TLabel').pack(anchor='w'); self.name_tree=ttk.Treeview(t,columns=('source','norm','vi','cat'),show='headings');
        for c,h in [('source','OCR'),('norm','Chuẩn'),('vi','Tiếng Việt'),('cat','Loại')]: self.name_tree.heading(c,text=h); self.name_tree.column(c,width=220)
        self.name_tree.pack(fill='both',expand=True); b=ttk.Frame(t); b.pack(fill='x',pady=8); ttk.Button(b,text='Thêm tên',command=self.add_name).pack(side='left'); ttk.Button(b,text='Nạp lại',command=self.refresh_names).pack(side='left',padx=8); self.refresh_names()
    def _mem_tab(self,t):
        ttk.Label(t,text='BẢNG OCR MEMORY — TẠM THỜI / CÓ THỂ XÓA',style='Step.TLabel').pack(anchor='w'); self.mem_tree=ttk.Treeview(t,columns=('obs','cor','conf'),show='headings');
        for c,h in [('obs','OCR sai'),('cor','Đã sửa'),('conf','Độ tin cậy')]: self.mem_tree.heading(c,text=h); self.mem_tree.column(c,width=280)
        self.mem_tree.pack(fill='both',expand=True); b=ttk.Frame(t); b.pack(fill='x',pady=8); ttk.Button(b,text='Xóa toàn bộ OCR Memory',command=self.clear_memory).pack(side='left'); ttk.Button(b,text='Nạp lại',command=self.refresh_memory).pack(side='left',padx=8); self.refresh_memory()
    def choose_video(self):
        p=filedialog.askopenfilename(title='Chọn video',filetypes=[('Video','*.mp4 *.mkv *.mov *.webm'),('MP4','*.mp4'),('All','*.*')]);
        if not p:return
        try:
            self.info=ffprobe(p); self.video=p; dur=float(self.info.get('format',{}).get('duration',0)); v=next((x for x in self.info.get('streams',[]) if x.get('width')),{})
            self.video_label.config(text='Video: '+Path(p).name); self.video_info.config(text=f'{Path(p).name} | {dur/60:.1f} phút | {v.get("width","?")}x{v.get("height","?")}'); self.logmsg('Đã nạp video: '+p)
        except Exception as e: messagebox.showerror('Video lỗi',str(e))
    def start_ocr(self):
        if not self.video:return messagebox.showwarning('Thiếu video','Hãy chọn video trước.')
        try:
            z={k:float(v.get()) for k,v in self.vars.items()}; self.region=(z['x'],z['y'],z['w'],z['h']); fps=max(.2,min(3,z['fps']))
            if not (0<=z['x']<=1 and 0<=z['y']<=1 and 0<z['w']<=1 and 0<z['h']<=1 and z['x']+z['w']<=1 and z['y']+z['h']<=1): raise ValueError('Vùng vượt ngoài khung hình')
        except Exception as e:return messagebox.showerror('Vùng OCR',str(e))
        threading.Thread(target=self._ocr_worker,args=(fps,),daemon=True).start()
    def _ocr_worker(self,fps):
        try:
            self.logmsg('Đang OCR...'); self.work=Path(tempfile.mkdtemp(prefix='vietdub_')); frames=extract_frames(self.video,self.work/'frames',fps); x,y,w,h=self.region; v=next(s for s in self.info['streams'] if s.get('width')); W,H=v['width'],v['height']; import cv2
            samples=[]
            for i,fr in enumerate(frames):
                im=cv2.imread(str(fr)); crop=im[int(y*H):int((y+h)*H),int(x*W):int((x+w)*W)]; cp=self.work/f'c_{i}.jpg'; cv2.imwrite(str(cp),crop); text,conf=ocr_image(str(cp)); samples.append((i/fps,text,conf))
                if i%10==0:self.after(0,self.status.config,text=f'OCR {i}/{len(frames)}')
            self.cues=build_cues(samples); self.apply_corrections(); self.after(0,self.populate); self.logmsg(f'OCR xong: {len(self.cues)} câu.')
        except Exception as e:self.after(0,lambda:messagebox.showerror('OCR lỗi',str(e)))
    def apply_corrections(self):
        proper=ProperNameDictionary(ROOT/'data/dictionaries/proper_names.json'); mem=OCRMemory(ROOT/'data/ocr_memory.json'); corr=OCRCorrector(proper,mem)
        for c in self.cues: c['corrected']=corr.correct(c['text']).corrected
    def populate(self):
        for i in self.tree.get_children():self.tree.delete(i)
        for c in self.cues:self.tree.insert('', 'end',iid=c['id'],values=(c['id'],f"{c['start']:.2f}",f"{c['end']:.2f}",c.get('corrected',c['text']),c.get('vietnamese',''),f"{c['confidence']:.2f}"))
        self.status.config(text=f'{len(self.cues)} câu'); self.refresh_memory()
    def edit_selected(self,event=None):
        sel=self.tree.selection()
        if not sel:return
        c=next((x for x in self.cues if x['id']==sel[0]),None)
        if not c:return
        old=c.get('corrected',c['text']); new=simpledialog.askstring('Sửa OCR','Tiếng Trung:',initialvalue=old,parent=self)
        if new is not None:c['corrected']=new
        vi=simpledialog.askstring('Sửa tiếng Việt','Bản dịch:',initialvalue=c.get('vietnamese',''),parent=self)
        if vi is not None:c['vietnamese']=vi
        self.populate()
    def translate_all(self):
        if not self.cues:return messagebox.showwarning('Chưa có OCR','Chạy OCR trước.')
        def w():
            try:
                tr=VietnameseTranslator()
                for i,c in enumerate(self.cues): c['vietnamese']=tr.translate(c.get('corrected',c['text'])); self.after(0,self.populate); self.after(0,self.status.config,text=f'Dịch {i+1}/{len(self.cues)}')
                self.logmsg('Dịch hoàn tất.')
            except Exception as e:self.after(0,lambda:messagebox.showerror('Dịch lỗi',str(e)))
        threading.Thread(target=w,daemon=True).start()
    def save_corrections(self):
        mem=OCRMemory(ROOT/'data/ocr_memory.json')
        for c in self.cues:
            obs=c['text']; cor=c.get('corrected',obs)
            if obs!=cor: mem.upsert(OCRCorrection(obs,cor,c.get('confidence'), 'GUI correction'))
        self.refresh_memory(); self.logmsg('Đã lưu các sửa OCR vào bộ nhớ tạm.')
    def add_name(self):
        src=simpledialog.askstring('Tên riêng','OCR / tên gốc:',parent=self)
        if not src:return
        norm=simpledialog.askstring('Tên chuẩn','Chữ Trung chuẩn:',initialvalue=src,parent=self) or src; vi=simpledialog.askstring('Tiếng Việt','Tên tiếng Việt:',parent=self)
        if not vi:return
        d=ProperNameDictionary(ROOT/'data/dictionaries/proper_names.json'); from .dictionary import ProperNameEntry; d.upsert(ProperNameEntry(src,norm,vi)); self.refresh_names()
    def refresh_names(self):
        if not hasattr(self,'name_tree'):return
        for i in self.name_tree.get_children():self.name_tree.delete(i)
        d=ProperNameDictionary(ROOT/'data/dictionaries/proper_names.json')
        for e in d.entries:self.name_tree.insert('', 'end',values=(e.source,e.normalized,e.vietnamese,e.category))
    def refresh_memory(self):
        if not hasattr(self,'mem_tree'):return
        for i in self.mem_tree.get_children():self.mem_tree.delete(i)
        m=OCRMemory(ROOT/'data/ocr_memory.json')
        for e in m.entries:self.mem_tree.insert('', 'end',values=(e.observed,e.corrected,e.confidence))
    def clear_memory(self):
        p=ROOT/'data/ocr_memory.json'; p.unlink(missing_ok=True); self.refresh_memory(); self.logmsg('Đã xóa OCR Memory.')
    def start_render(self):
        if not self.cues or any(not c.get('vietnamese') for c in self.cues):return messagebox.showwarning('Thiếu dữ liệu','Hãy OCR và dịch toàn bộ trước.')
        threading.Thread(target=self._render_worker,daemon=True).start()
    def _render_worker(self):
        try:
            td=self.work/'tts'; td.mkdir(exist_ok=True); files=[]
            for i,c in enumerate(self.cues): files.append(synthesize(c['vietnamese'],str(td/f'{i:05d}.mp3'),self.voice.get())); self.after(0,self.progress.config,value=40*(i+1)/len(self.cues))
            out=Path(self.video).with_name(Path(self.video).stem+'_VietDub.mp4'); render(self.video,self.cues,files,str(out),self.res.get(),mask_original=False); self.after(0,self.progress.config,value=100); self.after(0,lambda:messagebox.showinfo('Hoàn tất',f'Đã xuất:\n{out}')); self.logmsg('Xuất: '+str(out))
        except Exception as e:self.after(0,lambda:messagebox.showerror('Xuất lỗi',str(e)))

def main(): VietDubApp().mainloop(); return 0
