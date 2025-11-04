"""
將PNG轉換為ICO格式
用於Windows任務欄圖標
"""

from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    """將PNG轉換為ICO格式，包含多種尺寸"""
    try:
        # 打開PNG圖片
        img = Image.open(png_path)
        
        # 確保是RGBA模式（ICO需要）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 創建多種尺寸的圖片列表
        sizes = [16, 32, 48, 64, 128, 256]
        images = []
        
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            images.append(resized)
        
        # 保存為ICO格式（PIL會自動處理多尺寸）
        img.save(ico_path, format='ICO', sizes=[(s, s) for s in sizes])
        print(f"✓ 成功轉換: {png_path} -> {ico_path}")
        
        # 驗證文件
        if os.path.exists(ico_path):
            file_size = os.path.getsize(ico_path)
            print(f"✓ ICO檔案大小: {file_size / 1024:.2f} KB")
            return True
        else:
            print("✗ ICO檔案未建立")
            return False
            
    except Exception as e:
        import traceback
        print(f"✗ 轉換失敗: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    png_file = "RadioOne Logo.png"
    ico_file = "RadioOne Logo.ico"
    
    if os.path.exists(png_file):
        convert_png_to_ico(png_file, ico_file)
    else:
        print(f"✗ 找不到檔案: {png_file}")

