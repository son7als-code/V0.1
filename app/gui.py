from __future__ import annotations
import os, shutil, tempfile, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .media import ffprobe, extract_frames
from .ocr_engine import ocr_image, build_cues
from .translator import VietnameseTranslator
from .tts_engine import synthesize
from .render import render
from .dictionary import ProperNameDictionary, OCRMemory

ROOT=Path(__file__).resolve().parents[1]

class VietDubApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('VietDub AI - Chinese → Vietnamese Dubbing')
        self.geometry('1100x720'); self.minsize(900,620)
        self.video=None; self.info={}; self.frames=[]; self.region=None; self.cues=[]; self.work=None
        self._build()

    def _build(self):
        style=ttk.Style(self); style.configure('Title.TLabel',font=('Segoe UI',20,'bold')); style.configure('Step.TLabel',font=('Segoe UI',11,'bold'))
        top=ttk.Frame(self,padding=14); top.pack(fill='x')
        ttk.Label(top,text='VIETDUB AI',style='Title.TLabel').pack(side='left')
        ttk.Button(top,text='Chọn video MP4',command=self.choose_video).pack(side='right')
        self.video_label=ttk.Label(self,text='Chưa chọn video',padding=(16,4)); self.video_label.pack(fill='x')
        nb=ttk.Notebook(self); nb.pack(fill='both',expand=True,padx=12,pady=8)
        self.tab_video=ttk.Frame(nb,padding=12); self.tab_ocr=ttk.Frame(nb,padding=12); self.tab_edit=ttk.Frame(nb,padding=12); self.tab_run=ttk.Frame(nb,padding=12)
        for tab,name in [(self.tab_video,'1. VIDEO'),(self.tab_ocr,'2. VÙNG OCR'),(self.tab_edit,'3. OCR / DỊCH'),(self.tab_run,'4. TTS / XUẤT')]: nb.add(tab,text=name)
        self._video_tab(); self._ocr_tab(); self._edit_tab(); self._run_tab()
        self.log= tk.Text(self,height=8); self.log.pack(fill='x',padx=12,pady=(0,12)); self.log.configure(state='disabled')

    def logmsg(self,s):
        self.log.configure(state='normal'); self.log.insert('end',s+'\n'); self.log.see('end'); self.log.configure(state='disabled')

    def _video_tab(self):
        ttk.Label(self.tab_video,text='Video nguồn',style='Step.TLabel').pack(anchor='w')
        self.video_info=ttk.Label(self.tab_video,text='Chọn video để bắt đầu. Hỗ trợ MP4 và video dài 3 phút–3 giờ.'); self.video_info.pack(anchor='w',pady=8)
        ttk.Button(self.tab_video,text='Chọn video',command=self.choose_video).pack(anchor='w')

    def _ocr_tab(self):
        ttk.Label(self.tab_ocr,text='Khoanh vùng phụ đề bằng tọa độ phần trăm video',style='Step.TLabel').pack(anchor='w')
        f=ttk.Frame(self.tab_ocr); f.pack(anchor='w',pady=10)
        self.vars={k:tk.StringVar(value=v) for k,v in {'x':'0.05','y':'0.75','w':'0.90','h':'0.20','fps':'1'}.items()}
        for k in ['x','y','w','h','fps']:
            ttk.Label(f,text=k.upper()).pack(side='left'); ttk.Entry(f,textvariable=self.vars[k],width=7).pack(side='left',padx=(2,12))
        ttk.Button(self.tab_ocr,text='Chạy OCR',command=self.start_ocr).pack(anchor='w',pady=10)
        ttk.Label(self.tab_ocr,text='Nếu phụ đề nằm vị trí khác, sửa X/Y/W/H rồi chạy lại. OCR Memory sẽ ghi nhớ các lỗi bạn sửa.').pack(anchor='w')

    def _edit_tab(self):
        ttk.Label(self.tab_edit,text='Kết quả OCR → sửa → dịch tiếng Việt',style='Step.TLabel').pack(anchor='w')
        cols=('id','start','end','ocr','vi','conf')
        self.tree=ttk.Treeview(self.tab_edit,columns=cols,show='headings',height=18)
        names={'id':'#','start':'Bắt đầu','end':'Kết thúc','ocr':'Tiếng Trung (sửa được)','vi':'Tiếng Việt','conf':'OCR'}
        for c in cols: self.tree.heading(c,text=names[c]); self.tree.column(c,width=80 if c!='ocr' and c!='vi' else 300)
        self.tree.pack(fill='both',expand=True)
        ttk.Button(self.tab_edit,text='Dịch tất cả',command=self.translate_all).pack(anchor='w',pady=8)
        ttk.Button(self.tab_edit,text='Lưu câu đã sửa vào OCR Memory',command=self.save_corrections).pack(anchor='w')

    def _run_tab(self):
        ttk.Label(self.tab_run,text='TTS và xuất video',style='Step.TLabel').pack(anchor='w')
        f=ttk.Frame(self.tab_run); f.pack(anchor='w',pady=10)
        ttk.Label(f,text='Giọng:').pack(side='left'); self.voice=tk.StringVar(value='vi-VN-HoaiMyNeural'); ttk.Combobox(f,textvariable=self.voice,values=['vi-VN-HoaiMyNeural','vi-VN-NamMinhNeural'],width=28).pack(side='left',padx=8)
        ttk.Label(f,text='Độ phân giải:').pack(side='left'); self.res=tk.StringVar(value='1080p'); ttk.Combobox(f,textvariable=self.res,values=['720p','1080p','2K'],state='readonly',width=10).pack(side='left',padx=8)
        ttk.Button(self.tab_run,text='Tạo TTS + Xuất MP4',command=self.start_render).pack(anchor='w',pady=15)
        self.progress=ttk.Progressbar(self.tab_run,mode='determinate',maximum=100); self.progress.pack(fill='x')
        self.status=ttk.Label(self.tab_run,text='Sẵn sàng'); self.status.pack(anchor='w',pady=6)

    def choose_video(self):
        p=filedialog.askopenfilename(title='Chọn video',filetypes=[('Video MP4','*.mp4'),('Video','*.mp4 *.mkv *.mov *.webm'),('All files','*.*')])
        if not p:return
        try:
            self.info=ffprobe(p); self.video=p; dur=float(self.info.get('format',{}).get('duration',0)); streams=self.info.get('streams',[]); v=next((s for s in streams if s.get('width')),{})
            self.video_label.config(text=f'Video: {Path(p).name}')
            self.video_info.config(text=f'{Path(p).name} | {dur/60:.1f} phút | {v.get("width","?")}x{v.get("height","?")}')
            self.logmsg('Đã nạp video: '+p)
        except Exception as e: messagebox.showerror('Video lỗi',str(e))

    def start_ocr(self):
        if not self.video:return messagebox.showwarning('Thiếu video','Hãy chọn video trước.')
        try:
            vals={k:float(v.get()) for k,v in self.vars.items()}; self.region=(vals['x'],vals['y'],vals['w'],vals['h']); fps=max(.2,min(3,vals['fps']))
        except: return messagebox.showerror('Vùng OCR','X/Y/W/H/FPS phải là số.')
        threading.Thread(target=self._ocr_worker,args=(fps,),daemon=True).start()

    def _ocr_worker(self,fps):
        try:
            self.logmsg('Đang trích frame và OCR...')
            self.work=Path(tempfile.mkdtemp(prefix='vietdub_')); frames=extract_frames(self.video,self.work/'frames',fps); self.frames=frames
            x,y,w,h=self.region; streams=self.info.get('streams',[]); vs=next(s for s in streams if s.get('width')); W,H=vs['width'],vs['height']
            import cv2
            samples=[]
            for i,frame in enumerate(frames):
                im=cv2.imread(str(frame)); crop=im[int(y*H):int((y+h)*H),int(x*W):int((x+w)*W)]
                cp=self.work/f'c_{i}.jpg'; cv2.imwrite(str(cp),crop); text,conf=ocr_image(str(cp)); samples.append((i/fps,text,conf))
                if i%10==0:self.status.config(text=f'OCR {i}/{len(frames)}')
            self.cues=build_cues(samples); self.after(0,self.populate)
            self.logmsg(f'OCR xong: {len(self.cues)} câu thoại.')
        except Exception as e:self.after(0,lambda:messagebox.showerror('OCR lỗi',str(e)))

    def populate(self):
        for x in self.tree.get_children():self.tree.delete(x)
        for c in self.cues:self.tree.insert('', 'end',iid=c['id'],values=(c['id'],f"{c['start']:.2f}",f"{c['end']:.2f}",c['text'],'',f"{c['confidence']:.2f}"))
        self.status.config(text=f'Có {len(self.cues)} câu OCR')

    def translate_all(self):
        if not self.cues:return messagebox.showwarning('Chưa có OCR','Chạy OCR trước.')
        def worker():
            try:
                tr=VietnameseTranslator()
                for i,c in enumerate(self.cues):
                    c['vietnamese']=tr.translate(c['text']); self.after(0,self.populate); self.status.config(text=f'Dịch {i+1}/{len(self.cues)}')
                self.logmsg('Dịch hoàn tất.')
            except Exception as e:self.after(0,lambda:messagebox.showerror('Dịch lỗi',str(e)))
        threading.Thread(target=worker,daemon=True).start()

    def save_corrections(self):
        if not self.cues:return
        mem=OCRMemory(str(ROOT/'data'/'ocr_memory.json'))
        for c in self.cues: mem.upsert(c['text'],c['text'],c['confidence'],'GUI correction')
        self.logmsg('Đã lưu OCR Memory.')

    def start_render(self):
        if not self.cues or any(not c.get('vietnamese') for c in self.cues):return messagebox.showwarning('Thiếu dữ liệu','Hãy OCR và dịch toàn bộ trước.')
        threading.Thread(target=self._render_worker,daemon=True).start()

    def _render_worker(self):
        try:
            tdir=self.work/'tts'; tdir.mkdir(exist_ok=True); files=[]
            for i,c in enumerate(self.cues):
                p=str(tdir/f'{i:05d}.mp3'); synthesize(c['vietnamese'],p,self.voice.get()); files.append(p); self.after(0,lambda i=i:self.progress.config(value=40*i/max(1,len(self.cues))))
            out=Path(self.video).with_name(Path(self.video).stem+'_VietDub.mp4'); render(self.video,self.cues,files,str(out),self.res.get(),mask_original=False)
            self.after(0,lambda:messagebox.showinfo('Hoàn tất',f'Đã xuất:\n{out}')); self.logmsg('Xuất video: '+str(out)); self.progress.config(value=100)
        except Exception as e:self.after(0,lambda:messagebox.showerror('Xuất lỗi',str(e)))

def main():
    app=VietDubApp(); app.mainloop(); return 0
