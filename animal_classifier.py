import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
import hashlib
import json


CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.animal_classifier_config.json')


def get_file_hash(file_path):
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()[:16]


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'保存配置失败: {e}')


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f'加载配置失败: {e}')
    return {}


class AnimalFileMigratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('动物文件分类迁移工具')
        self.root.geometry('700x680')
        
        self.selected_files = []
        self.taxonomy_entries = {}
        
        self.setup_ui()
        self.load_config_to_ui()
        
        # 监听分类输入框变化，自动保存
        for key in self.taxonomy_entries:
            self.taxonomy_entries[key].bind('<KeyRelease>', self.auto_save_config)
        self.target_dir_entry.bind('<KeyRelease>', self.auto_save_config)
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding='20')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 学名输入和查询
        ttk.Label(main_frame, text='物种名:', font=('微软雅黑', 11)).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.species_name_entry = ttk.Entry(main_frame, font=('微软雅黑', 11))
        self.species_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=10, padx=10)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=0, column=2, sticky=tk.W, pady=10)
        
        self.query_btn = ttk.Button(btn_frame, text='查询', command=self.query_species)
        self.query_btn.pack(side=tk.LEFT, padx=2)
        
        self.save_btn = ttk.Button(btn_frame, text='保存', command=self.save_species)
        self.save_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(main_frame, text='分类信息:', font=('微软雅黑', 11)).grid(row=1, column=0, sticky=tk.NW, pady=10)
        
        taxonomy_frame = ttk.Frame(main_frame)
        taxonomy_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=10, padx=10)
        
        taxonomy_keys = ['界', '门', '纲', '目', '科', '属', '种']
        for i, key in enumerate(taxonomy_keys):
            ttk.Label(taxonomy_frame, text=f'{key}:', font=('微软雅黑', 10)).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(taxonomy_frame, font=('微软雅黑', 10))
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
            self.taxonomy_entries[key] = entry
        
        taxonomy_frame.columnconfigure(1, weight=1)
        
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        ttk.Label(main_frame, text='选择文件:', font=('微软雅黑', 11)).grid(row=3, column=0, sticky=tk.W, pady=10)
        self.select_files_btn = ttk.Button(main_frame, text='浏览文件', command=self.select_files)
        self.select_files_btn.grid(row=3, column=1, sticky=tk.W, pady=10, padx=10)
        
        self.files_listbox = tk.Listbox(main_frame, height=6, font=('微软雅黑', 10))
        self.files_listbox.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=10)
        
        ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        ttk.Label(main_frame, text='目标根目录:', font=('微软雅黑', 11)).grid(row=6, column=0, sticky=tk.W, pady=10)
        self.target_dir_entry = ttk.Entry(main_frame, font=('微软雅黑', 11))
        self.target_dir_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=10, padx=10)
        default_dir = os.path.join(os.path.expanduser('~'), 'Desktop', '动物分类')
        self.target_dir_entry.insert(0, default_dir)
        
        self.select_target_btn = ttk.Button(main_frame, text='选择目录', command=self.select_target_dir)
        self.select_target_btn.grid(row=6, column=2, pady=10)
        
        self.migrate_btn = ttk.Button(main_frame, text='开始迁移', command=self.start_migration, state='disabled')
        self.migrate_btn.grid(row=7, column=0, columnspan=3, pady=20)
        
        main_frame.rowconfigure(4, weight=1)
    
    def load_config_to_ui(self):
        config = load_config()
        
        # 加载分类信息
        for key in self.taxonomy_entries:
            if key in config:
                self.taxonomy_entries[key].delete(0, tk.END)
                self.taxonomy_entries[key].insert(0, config[key])
        
        # 加载目标目录
        if 'target_dir' in config:
            self.target_dir_entry.delete(0, tk.END)
            self.target_dir_entry.insert(0, config['target_dir'])
        
        self.check_can_migrate()
    
    def auto_save_config(self, event=None):
        config = load_config()
        
        # 保存分类信息
        for key in self.taxonomy_entries:
            config[key] = self.taxonomy_entries[key].get().strip()
        
        # 保存目标目录
        config['target_dir'] = self.target_dir_entry.get().strip()
        
        save_config(config)
        self.check_can_migrate()
    
    def query_species(self):
        species_name = self.species_name_entry.get().strip()
        if not species_name:
            messagebox.showwarning('提示', '请输入物种名')
            return
        
        config = load_config()
        species_records = config.get('species_records', {})
        
        if species_name in species_records:
            record = species_records[species_name]
            # 填充分类信息
            for key in ['界', '门', '纲', '目', '科', '属', '种']:
                if key in record:
                    self.taxonomy_entries[key].delete(0, tk.END)
                    self.taxonomy_entries[key].insert(0, record[key])
            messagebox.showinfo('成功', f'已加载「{species_name}」的分类信息')
            self.auto_save_config()
        else:
            messagebox.showinfo('提示', f'未找到「{species_name}」的记录，请先保存')
    
    def save_species(self):
        species_name = self.species_name_entry.get().strip()
        if not species_name:
            messagebox.showwarning('提示', '请输入物种名')
            return
        
        # 检查分类信息是否完整
        for key in ['界', '门', '纲', '目', '科', '属', '种']:
            if not self.taxonomy_entries[key].get().strip():
                messagebox.showwarning('提示', f'请先填写「{key}」的分类信息')
                return
        
        config = load_config()
        if 'species_records' not in config:
            config['species_records'] = {}
        
        # 保存当前分类信息
        record = {}
        for key in ['界', '门', '纲', '目', '科', '属', '种']:
            record[key] = self.taxonomy_entries[key].get().strip()
        
        config['species_records'][species_name] = record
        save_config(config)
        
        messagebox.showinfo('成功', f'已保存「{species_name}」的分类信息')
    
    def select_files(self):
        files = filedialog.askopenfilenames(title='选择要迁移的文件')
        if files:
            self.selected_files = list(files)
            self.files_listbox.delete(0, tk.END)
            for f in self.selected_files:
                self.files_listbox.insert(tk.END, os.path.basename(f))
            self.check_can_migrate()
    
    def select_target_dir(self):
        dir_path = filedialog.askdirectory(title='选择目标根目录')
        if dir_path:
            self.target_dir_entry.delete(0, tk.END)
            self.target_dir_entry.insert(0, dir_path)
            self.auto_save_config()
    
    def check_can_migrate(self):
        has_taxonomy = True
        for key in self.taxonomy_entries:
            if not self.taxonomy_entries[key].get().strip():
                has_taxonomy = False
                break
        if has_taxonomy and self.selected_files:
            self.migrate_btn.config(state='normal')
        else:
            self.migrate_btn.config(state='disabled')
    
    def start_migration(self):
        if not self.selected_files:
            return
        
        taxonomy = {}
        for key in self.taxonomy_entries:
            taxonomy[key] = self.taxonomy_entries[key].get().strip()
            if not taxonomy[key]:
                messagebox.showwarning('提示', f'请填写{key}的分类信息')
                return
        
        target_root = self.target_dir_entry.get().strip()
        if not target_root:
            messagebox.showwarning('提示', '请选择目标根目录')
            return
        
        try:
            taxonomy_path = os.path.join(
                target_root,
                taxonomy['界'],
                taxonomy['门'],
                taxonomy['纲'],
                taxonomy['目'],
                taxonomy['科'],
                taxonomy['属'],
                taxonomy['种']
            )
            
            os.makedirs(taxonomy_path, exist_ok=True)
            
            success_count = 0
            for file_path in self.selected_files:
                if not os.path.exists(file_path):
                    continue
                
                file_ext = os.path.splitext(file_path)[1]
                file_hash = get_file_hash(file_path)
                new_filename = f'{taxonomy["种"]}_{file_hash}{file_ext}'
                new_file_path = os.path.join(taxonomy_path, new_filename)
                
                # 移动文件而不是复制
                shutil.move(file_path, new_file_path)
                success_count += 1
            
            messagebox.showinfo('完成', f'成功迁移 {success_count} 个文件到:\n{taxonomy_path}')
            
        except Exception as e:
            messagebox.showerror('错误', f'迁移失败: {str(e)}')


def main():
    root = tk.Tk()
    app = AnimalFileMigratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
