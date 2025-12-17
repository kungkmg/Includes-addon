import os
import json
import uuid
import shutil
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

# --- CONFIGURATION ---
TEMP_DIR = "temp_runaeshike_workspace"
OUTPUT_NAME = "Runaeshike_Merged_Addon"
CREDIT_NAME = "Runaeshike 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹"
SIGNATURE_KEY = "_protected_by"

class UltimateMerger:
    def __init__(self):
        self.bp_path = Path(TEMP_DIR) / "behavior_pack"
        self.rp_path = Path(TEMP_DIR) / "resource_pack"
        
        # ตัวแปรสำหรับเก็บข้อมูลที่ต้อง Merge (รวมกัน)
        self.merged_item_textures = {}
        self.merged_terrain_textures = {}
        self.merged_sound_defs = {} # เพิ่มการรวมเสียง
        self.merged_lang_data = []
        self.merged_blocks_def = {}
        
        self.found_bp = False
        self.found_rp = False
        self.custom_icon_path = None
        self.new_bp_uuid = str(uuid.uuid4())
        self.new_rp_uuid = str(uuid.uuid4())

    def reset_workspace(self):
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(self.bp_path, exist_ok=True)
        os.makedirs(self.rp_path, exist_ok=True)

    def load_json(self, path):
        """ อ่านไฟล์ JSON แบบปลอดภัย ถ้าอ่านไม่ได้ให้ Return None """
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lstrip('\ufeff')
                # ลบ Comment แบบ // ออก เพื่อให้ json.loads ทำงานได้
                lines = [l for l in content.splitlines() if not l.strip().startswith("//")]
                return json.loads("\n".join(lines))
        except Exception as e:
            # ถ้าอ่านไม่ออก (ไฟล์โมเดลแปลกๆ) ให้ส่งกลับเป็น None เพื่อให้ระบบใช้วิธีก๊อปปี้ธรรมดา
            return None

    def save_encrypted_json(self, data, file_path):
        """ บันทึกไฟล์แบบเข้ารหัส (Minify + Signature) """
        if isinstance(data, dict):
            data[SIGNATURE_KEY] = CREDIT_NAME
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # separators=(',', ':') ช่วยบีบอัดไฟล์ให้เล็กที่สุด (Minify)
                json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:
            print(f"Error saving json: {e}")

    def merge_json_data(self, source_path, file_type):
        data = self.load_json(source_path)
        if data is None: return # ข้ามถ้าไฟล์เสีย

        if file_type == 'item_texture': 
            self.merged_item_textures.update(data.get('texture_data', {}))
        elif file_type == 'terrain_texture': 
            self.merged_terrain_textures.update(data.get('texture_data', {}))
        elif file_type == 'sound_definitions':
            self.merged_sound_defs.update(data.get('sound_definitions', {}))
        elif file_type == 'blocks':
            for k, v in data.items():
                if k != 'format_version': self.merged_blocks_def[k] = v

    def merge_lang_file(self, source_path):
        try:
            with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.merged_lang_data.append(f.read() + "\n")
        except: pass

    def recursive_copy_and_merge(self, src_folder, dst_folder, is_resource_pack):
        for root, dirs, files in os.walk(src_folder):
            rel_path = os.path.relpath(root, src_folder)
            target_dir = os.path.join(dst_folder, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                file_lower = file.lower()
                dest_file = os.path.join(target_dir, file)

                # ข้ามไฟล์ที่ไม่จำเป็น
                if file_lower in ['manifest.json', 'pack_icon.png', 'pack_icon.jpeg', 'pack_icon.jpg']: 
                    continue

                # --- จัดการไฟล์ Resource Pack ที่ต้องรวมเนื้อหา ---
                if is_resource_pack:
                    if file_lower == 'item_texture.json': 
                        self.merge_json_data(src_file, 'item_texture')
                        continue
                    elif file_lower == 'terrain_texture.json': 
                        self.merge_json_data(src_file, 'terrain_texture')
                        continue
                    elif file_lower == 'sound_definitions.json': # รองรับเสียง
                        self.merge_json_data(src_file, 'sound_definitions')
                        continue
                    elif file_lower.endswith('.lang'): 
                        self.merge_lang_file(src_file)
                        continue
                    elif file_lower == 'blocks.json': 
                        self.merge_json_data(src_file, 'blocks')
                        continue

                # --- ไฟล์อื่นๆ (Models, Entities, Animations) ---
                if file_lower.endswith('.json'):
                    # พยายามอ่านและเข้ารหัส
                    data = self.load_json(src_file)
                    
                    if data is not None:
                        # ถ้าอ่านได้ปกติ -> เข้ารหัสและบันทึก
                        self.save_encrypted_json(data, dest_file)
                    else:
                        # [แก้บัคโมเดลใหญ่] ถ้าอ่าน JSON ไม่ได้ (ซับซ้อนเกิน/ผิด Format) -> ก๊อปปี้ไปดื้อๆ เลย (ปลอดภัยกว่า)
                        # print(f"Warning: Copying raw file (complex model?): {file}")
                        shutil.copy2(src_file, dest_file)
                else:
                    # ไฟล์ที่ไม่ใช่ JSON (รูปภาพ .png, .tga, .fsb) ก๊อปปี้เลย
                    shutil.copy2(src_file, dest_file)

    def write_merged_special_files(self):
        # สร้าง item_texture.json
        if self.merged_item_textures:
            out = {"resource_pack_name": "runaeshike_pack", "texture_name": "atlas.items", "texture_data": self.merged_item_textures}
            os.makedirs(self.rp_path / "textures", exist_ok=True)
            self.save_encrypted_json(out, self.rp_path / "textures" / "item_texture.json")
        
        # สร้าง terrain_texture.json
        if self.merged_terrain_textures:
            out = {"resource_pack_name": "runaeshike_pack", "texture_name": "atlas.terrain", "texture_data": self.merged_terrain_textures}
            os.makedirs(self.rp_path / "textures", exist_ok=True)
            self.save_encrypted_json(out, self.rp_path / "textures" / "terrain_texture.json")
            
        # สร้าง blocks.json
        if self.merged_blocks_def:
            out = {"format_version": [1, 1, 0], **self.merged_blocks_def}
            self.save_encrypted_json(out, self.rp_path / "blocks.json")

        # สร้าง sound_definitions.json (แก้บัคเสียงหาย)
        if self.merged_sound_defs:
            out = {"format_version": "1.14.0", "sound_definitions": self.merged_sound_defs}
            os.makedirs(self.rp_path / "sounds", exist_ok=True)
            self.save_encrypted_json(out, self.rp_path / "sounds" / "sound_definitions.json")

        # สร้างไฟล์ภาษา .lang
        if self.merged_lang_data:
            os.makedirs(self.rp_path / "texts", exist_ok=True)
            with open(self.rp_path / "texts" / "en_US.lang", 'w', encoding='utf-8') as f:
                f.write("".join(self.merged_lang_data) + f"\n## Protected by {CREDIT_NAME} ##")
            # สร้าง languages.json เพื่อบอกเกมว่ามีภาษาอะไรบ้าง
            with open(self.rp_path / "texts" / "languages.json", 'w', encoding='utf-8') as f:
                json.dump(["en_US"], f)

    def create_manifest(self, path, base_name, uuid_own, uuid_dep=None, is_rp=False):
        m_type = "resources" if is_rp else "data"
        manifest = {
            "format_version": 2,
            "header": {
                "name": f"{base_name} | {CREDIT_NAME}",
                "description": f"Addon Merged & Protected by {CREDIT_NAME}.",
                "uuid": uuid_own,
                "version": [1, 0, 0],
                "min_engine_version": [1, 20, 0]
            },
            "modules": [{"type": m_type, "uuid": str(uuid.uuid4()), "version": [1, 0, 0]}],
            "metadata": {"authors": [CREDIT_NAME], "license": "Closed Source / Protected"}
        }
        if uuid_dep: manifest["dependencies"] = [{"uuid": uuid_dep, "version": [1, 0, 0]}]
        self.save_encrypted_json(manifest, path / "manifest.json")

    def set_icon(self, target_path):
        if self.custom_icon_path and os.path.exists(self.custom_icon_path):
            try:
                shutil.copy2(self.custom_icon_path, target_path / "pack_icon.png")
            except: pass

    def process(self, file_paths, icon_path):
        self.reset_workspace()
        self.custom_icon_path = icon_path
        
        for fp in file_paths:
            print(f"Processing: {fp}")
            temp_extract = Path(TEMP_DIR) / "extract_temp"
            try:
                with zipfile.ZipFile(fp, 'r') as z: z.extractall(temp_extract)
            except:
                print(f"Skipping bad zip: {fp}")
                continue

            # ค้นหา Manifest เพื่อระบุประเภท Pack
            for root, dirs, files in os.walk(temp_extract):
                if 'manifest.json' in files:
                    try:
                        m = self.load_json(os.path.join(root, 'manifest.json'))
                        if m:
                            modules = m.get('modules', [])
                            is_rp = any(mod['type'] == 'resources' for mod in modules)
                            if is_rp: 
                                self.found_rp = True
                                self.recursive_copy_and_merge(root, self.rp_path, True)
                            else: 
                                self.found_bp = True
                                self.recursive_copy_and_merge(root, self.bp_path, False)
                    except Exception as e: 
                        print(f"Manifest error: {e}")
            
            # ลบ Temp ย่อย
            try: shutil.rmtree(temp_extract)
            except: pass

        self.write_merged_special_files()
        
        # สร้าง Manifest ใหม่
        if self.found_bp:
            dep = self.new_rp_uuid if self.found_rp else None
            self.create_manifest(self.bp_path, "Behavior", self.new_bp_uuid, dep, False)
            self.set_icon(self.bp_path)
        
        if self.found_rp:
            dep = self.new_bp_uuid if self.found_bp else None
            self.create_manifest(self.rp_path, "Resource", self.new_rp_uuid, dep, True)
            self.set_icon(self.rp_path)

        # Zip ไฟล์เป็น .mcaddon
        output_file = f"{OUTPUT_NAME}.mcaddon"
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as z:
            for p_path, p_name in [(self.bp_path, "behavior_pack"), (self.rp_path, "resource_pack")]:
                if os.path.exists(p_path):
                    for root, dirs, files in os.walk(p_path):
                        for file in files:
                            p = os.path.join(root, file)
                            z.write(p, os.path.join(p_name, os.path.relpath(p, p_path)))
        
        self.reset_workspace()
        return output_file

def run_main_system():
    root = tk.Tk()
    root.title(f"{CREDIT_NAME} - Addon Encryptor & Merger (Safe Mode)")
    root.geometry("450x350")
    root.configure(bg="#1e1e1e")

    selected_files = []
    selected_icon = [None]

    def select_addons():
        files = filedialog.askopenfilenames(filetypes=[("MC Addons", "*.mcaddon *.mcpack *.zip")])
        if files:
            selected_files.clear()
            selected_files.extend(files)
            lbl_files.config(text=f"เลือกแล้ว: {len(files)} ไฟล์", fg="#4CAF50")

    def select_icon():
        f = filedialog.askopenfilename(filetypes=[("Image", "*.png *.jpg")])
        if f:
            selected_icon[0] = f
            lbl_icon.config(text=f"Icon: {os.path.basename(f)}", fg="#4CAF50")

    def start_process():
        if not selected_files:
            messagebox.showwarning("เตือน", "กรุณาเลือกไฟล์ Addon ก่อน")
            return
        try:
            merger = UltimateMerger()
            out = merger.process(selected_files, selected_icon[0])
            messagebox.showinfo("เสร็จสิ้น", f"สร้างไฟล์สำเร็จ!\nบันทึกชื่อ: {out}")
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {str(e)}")

    tk.Label(root, text="Runaeshike Addon Merger", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#00e5ff").pack(pady=10)
    tk.Label(root, text="ระบบรองรับโมเดลใหญ่ + แก้บัค 100%", font=("Arial", 10), bg="#1e1e1e", fg="#aaaaaa").pack()
    
    frame = tk.Frame(root, bg="#1e1e1e")
    frame.pack(pady=20)
    
    tk.Button(frame, text="1. เลือกไฟล์ Addons", command=select_addons, width=20, bg="#333", fg="white").grid(row=0, column=0, padx=10)
    lbl_files = tk.Label(frame, text="ยังไม่ได้เลือก", bg="#1e1e1e", fg="gray")
    lbl_files.grid(row=1, column=0)
    
    tk.Button(frame, text="2. เลือกรูป Icon", command=select_icon, width=20, bg="#333", fg="white").grid(row=0, column=1, padx=10)
    lbl_icon = tk.Label(frame, text="ใช้ Default", bg="#1e1e1e", fg="gray")
    lbl_icon.grid(row=1, column=1)
    
    tk.Button(root, text="START MERGE & ENCRYPT", command=start_process, font=("Arial", 12, "bold"), bg="#d500f9", fg="white", width=30).pack(pady=20)
    
    root.mainloop()