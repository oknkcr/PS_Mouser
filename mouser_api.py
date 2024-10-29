import requests
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename
import webbrowser  # URL'yi açmak için gerekli

def load_api_key():
    try:
        with open("api_key.txt", "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        messagebox.showerror("Hata", "api_key.txt dosyası bulunamadı.")
        return None

def load_info_text():
    try:
        with open("info.txt", "r") as file:
            return file.read()
    except FileNotFoundError:
        return "info.txt dosyası bulunamadı."

api_key = load_api_key()

def fetch_data(part_number):
    if not api_key:
        return None
    url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
    params = {
        "SearchByPartRequest": {
            "mouserPartNumber": part_number
        }
    }
    response = requests.post(url, json=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("Errors"):
            messagebox.showerror("Hata", data["Errors"][0]["Message"])
            return None
        else:
            return data.get("SearchResults", {}).get("Parts", [])
    else:
        messagebox.showerror("API Hatası", f"Hata kodu: {response.status_code}")
        return None

def create_gui():
    root = tk.Tk()
    root.title("Mouser Parça Arama")
    root.geometry("850x750")

    style = ttk.Style(root)
    root.configure(bg='#E8F0F2')
    style.configure("TNotebook", background="#D6EAF8", borderwidth=0)
    style.configure("TNotebook.Tab", font=("Helvetica", 10, "bold"), padding=[15, 8])
    style.map("TNotebook.Tab", background=[("selected", "#3498DB")])

    frame = tk.Frame(root, bg='#E8F0F2')
    frame.pack(pady=10)

    tk.Label(frame, text="Parça Numarası:", font=("Helvetica", 11), bg='#E8F0F2').grid(row=0, column=0, padx=5)
    part_number_entry = tk.Entry(frame, width=30, font=("Helvetica", 11))
    part_number_entry.grid(row=0, column=1, padx=5)

    notebook = ttk.Notebook(root, style="TNotebook")
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    def show_info():
        info_text = load_info_text()
        messagebox.showinfo("Info", info_text)

    search_button = tk.Button(frame, text="Ara", font=("Helvetica", 11), command=lambda: search_and_display(part_number_entry.get()), bg='#3498DB', fg='white')
    search_button.grid(row=0, column=2, padx=5)

    info_button = tk.Button(frame, text="Info", font=("Helvetica", 11), command=show_info, bg='#58D68D', fg='white')
    info_button.grid(row=0, column=3, padx=5)

    def search_and_display(part_number):
        for widget in notebook.winfo_children():
            widget.destroy()

        parts = fetch_data(part_number)
        if parts:
            displayed_tabs = []
            parts_list = []

            # Listbox ve arama alanı
            listbox_frame = tk.Frame(root, bg="#E8F0F2")
            listbox_frame.pack(fill="both", expand=False)
            tk.Label(listbox_frame, text="Sonuçlar:", font=("Helvetica", 11, "bold"), bg="#E8F0F2").pack(side="left")

            listbox = tk.Listbox(listbox_frame, font=("Helvetica", 10), width=50, height=8)
            listbox.pack(side="left", padx=10)

            # Listbox için arama alanı
            tk.Label(listbox_frame, text="P/N:", font=("Helvetica", 11, "bold"), bg="#E8F0F2", fg="#FF0000").pack(side="left")
            
            filter_listbox_entry = tk.Entry(listbox_frame, font=("Helvetica", 10), width=30)
            filter_listbox_entry.pack(side="left", padx=10)

            for i, item in enumerate(parts):
                parts_list.append(item)  # Tüm parçaları sakla
                listbox.insert("end", f"{item['ManufacturerPartNumber']}")

            listbox.bind("<<ListboxSelect>>", lambda event: update_tab(listbox.get(listbox.curselection())))

            if len(parts) > 0:
                displayed_tabs.append(create_tab(parts[0]))
                notebook.select(displayed_tabs[0])

            download_button = tk.Button(root, text="Excel İndir", font=("Helvetica", 11), command=lambda: save_to_excel(parts, part_number), bg='#2ECC71', fg='white')
            download_button.pack(pady=10)

            def update_tab(selected_manufacturer_part_number):
         
                if selected_manufacturer_part_number == "":
                   return
                # Seçilen parça numarasına göre parçayı bul
                selected_part = next((part for part in parts if part['ManufacturerPartNumber'] == selected_manufacturer_part_number), None)
    
                if selected_part:
                # Eğer tab mevcutsa, sil
                    if len(notebook.tabs()) > 0:
                        notebook.forget(notebook.tabs()[0])  # İlk tabı sil

                    # Yeni tab oluştur
                    new_tab = create_tab(selected_part)
                    notebook.add(new_tab, text=selected_part.get("ManufacturerPartNumber", "Sonuç"))
                    notebook.select(new_tab)

            # Listbox'ta arama yapma fonksiyonu
            def filter_listbox(event):
                search_term = filter_listbox_entry.get().lower()
                listbox.delete(0, "end")  # Listbox'ı temizle
                for part in parts:
                    if search_term in part['ManufacturerPartNumber'].lower():
                        listbox.insert("end", part['ManufacturerPartNumber'])
   
            filter_listbox_entry.bind("<KeyRelease>", filter_listbox)

    def create_tab(part_data):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=part_data.get("ManufacturerPartNumber", "Sonuç"))

        details = [
            ("Mouser Part Number", part_data.get("MouserPartNumber", "Mevcut değil")),
            ("Manufacturer Part Number", part_data.get("ManufacturerPartNumber", "Mevcut değil")),
            ("Manufacturer", part_data.get("Manufacturer", "Mevcut değil")),
            ("Availability", part_data.get("Availability", "Stok bilgisi mevcut değil")),
            ("Data Sheet URL", part_data.get("DataSheetUrl", "Datasheet mevcut değil")),
            ("Part Description", part_data.get("Description", "Mevcut değil")),
            ("Image URL", part_data.get("ImagePath", "Görsel mevcut değil")),
            ("Product Category", part_data.get("MouserProductCategory", "Kategori mevcut değil")),
            ("Packaging", part_data.get("Packaging", "Paketleme bilgisi mevcut değil")),
            ("Lifecycle Status", part_data.get("LifecycleStatus", "Durum mevcut değil")),
            ("RoHS Status", part_data.get("ROHSStatus", "RoHS durumu mevcut değil")),
            ("Reeling Availability", part_data.get("Reeling", False)),
            ("Minimum Order Quantity", part_data.get("Min", "Minimum sipariş miktarı mevcut değil")),
            ("Order Quantity Multiples", part_data.get("Mult", "Sipariş miktarları mevcut değil")),
            ("Lead Time", part_data.get("LeadTime", "Lead time mevcut değil")),
            ("Suggested Replacement(s)", part_data.get("SuggestedReplacement", "Tavsiye edilen değişim mevcut değil")),
            ("Product Detail Page URL", part_data.get("ProductDetailUrl", "Detay sayfası mevcut değil")),
        ]

        search_frame = tk.Frame(tab)
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="Filtrele:", font=("Helvetica", 10, "bold")).pack(side="left")
        filter_entry = tk.Entry(search_frame, font=("Helvetica", 10))
        filter_entry.pack(side="left", padx=10)

        text = tk.Text(tab, wrap="word", bg="#F8F9F9", font=("Helvetica", 10))
        for label, value in details:
            if "URL" in label:
                text.insert("end", f"{label}: ", "bold")
                text.insert("end", f"{value}\n\n", "link")
                text.tag_bind("link", "<Button-1>", lambda e, url=value: webbrowser.open(url))
            else:
                text.insert("end", f"{label}: {value}\n\n")

        text.tag_configure("link", foreground="blue", underline=True)
        text.tag_configure("bold", font=("Helvetica", 10, "bold"))
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        def apply_filter(event=None):
            text.config(state="normal")
            text.delete("1.0", "end")
            keyword = filter_entry.get().lower()
            for label, value in details:
                if keyword in label.lower() or keyword in str(value).lower():
                    if "URL" in label:
                        text.insert("end", f"{label}: ", "bold")
                        text.insert("end", f"{value}\n\n", "link")
                        text.tag_bind("link", "<Button-1>", lambda e, url=value: webbrowser.open(url))
                    else:
                        text.insert("end", f"{label}: {value}\n\n")
            text.config(state="disabled")

        filter_entry.bind("<KeyRelease>", apply_filter)
        return tab

    def save_to_excel(parts, part_number):
        df = pd.DataFrame(parts)
        save_path = asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")],
                                       initialfile=f"{part_number}.xlsx")
        if save_path:
            df.to_excel(save_path, index=False)
            messagebox.showinfo("Başarılı", "Excel dosyası başarıyla kaydedildi.")

    root.mainloop()

if __name__ == "__main__":
    create_gui()
