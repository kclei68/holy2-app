import flet as ft
import sqlite3
import datetime
import urllib.parse
import csv
import os

def init_db():
    conn = sqlite3.connect('holy_communion.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, name TEXT NOT NULL, gender TEXT, age TEXT, phone TEXT,
            contact_person TEXT, address TEXT, apply_date TEXT, normal_host BOOLEAN,
            minister_name TEXT, minister_phone TEXT, frequency TEXT, remarks TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def main(page: ft.Page):
    page.title = "外送聖體登記系統"
    page.window_width = 400
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- [新增登記分頁] ---
    name_input = ft.TextField(label="教友姓名 (必填)")
    gender_dropdown = ft.Dropdown(label="性別", options=[ft.dropdown.Option("男"), ft.dropdown.Option("男")])
    age_input = ft.TextField(label="年齡", keyboard_type=ft.KeyboardType.NUMBER)
    phone_input = ft.TextField(label="聯絡電話", keyboard_type=ft.KeyboardType.PHONE)
    contact_person_input = ft.TextField(label="聯絡人 (如非本人)")
    address_input = ft.TextField(label="外送地址", multiline=True)
    date_input = ft.TextField(label="申請日期 (YYYY-MM-DD)")
    normal_host_checkbox = ft.Checkbox(label="正常領一個聖體", value=True)
    minister_name_input = ft.TextField(label="負責聖體員姓名")
    minister_phone_input = ft.TextField(label="聖體員電話", keyboard_type=ft.KeyboardType.PHONE)
    frequency_dropdown = ft.Dropdown(label="外送頻次", options=[
        ft.dropdown.Option("每週一次"), ft.dropdown.Option("雙週一次"), ft.dropdown.Option("每月一次"), ft.dropdown.Option("按個別需要")
    ])
    remarks_input = ft.TextField(label="備註資料", multiline=True)

    def submit_click(e):
        if not name_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("請填寫教友姓名！"), bgcolor=ft.colors.RED_600)
            page.snack_bar.open = True
            page.update()
            return
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect('holy_communion.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO registry (
                    timestamp, name, gender, age, phone, contact_person, 
                    address, apply_date, normal_host, minister_name, 
                    minister_phone, frequency, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_time, name_input.value, gender_dropdown.value, age_input.value, 
                phone_input.value, contact_person_input.value, address_input.value, 
                date_input.value, normal_host_checkbox.value, minister_name_input.value, 
                minister_phone_input.value, frequency_dropdown.value, remarks_input.value
            ))
            conn.commit()
            conn.close()
            page.snack_bar = ft.SnackBar(ft.Text("登記成功！"), bgcolor=ft.colors.GREEN_600)
            for control in [name_input, phone_input, address_input, remarks_input]:
                control.value = ""
            load_records()
        except Exception as error:
            page.snack_bar = ft.SnackBar(ft.Text(f"錯誤: {error}"), bgcolor=ft.colors.RED_600)
        finally:
            page.snack_bar.open = True
            page.update()

    submit_btn = ft.ElevatedButton("儲存資料", on_click=submit_click, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE))

    form_view = ft.Column(
        controls=[
            ft.Text("送聖體服務登記表", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_800),
            ft.Divider(), name_input, gender_dropdown, age_input, phone_input, 
            contact_person_input, address_input, date_input, normal_host_checkbox, ft.Divider(),
            minister_name_input, minister_phone_input, frequency_dropdown, remarks_input, submit_btn
        ],
        expand=True, scroll=ft.ScrollMode.AUTO, visible=True
    )

    # --- [名單瀏覽分頁] ---
    def export_to_csv(e):
        try:
            conn = sqlite3.connect('holy_communion.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM registry")
            rows = cursor.fetchall()
            conn.close()
            download_path = "/storage/emulated/0/Download"
            if not os.path.exists(download_path):
                download_path = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(download_path, exist_ok=True)
            filename = f"聖體登記名單_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            filepath = os.path.join(download_path, filename)
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', '建立時間', '教友姓名', '性別', '年齡', '電話', '聯絡人', '地址', '申請日期', '正常領一聖體', '聖體員', '聖體員電話', '頻次', '備註'])
                writer.writerows(rows)
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ 成功匯出！\n已儲存至 Download 資料夾"), bgcolor=ft.colors.GREEN_600)
        except Exception as error:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ 匯出失敗: {error}"), bgcolor=ft.colors.RED_600)
        finally:
            page.snack_bar.open = True
            page.update()

    export_btn = ft.IconButton(
        icon=ft.icons.DOWNLOAD_FOR_OFFLINE, icon_color=ft.colors.GREEN_600, 
        tooltip="匯出成 CSV", on_click=export_to_csv
    )

    list_header = ft.Row(
        controls=[ft.Text("教友登記名單", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_800), export_btn],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    search_input = ft.TextField(
        label="搜尋姓名或地址...", prefix_icon=ft.icons.SEARCH, on_change=lambda e: load_records()
    )
    
    records_list = ft.ListView(expand=True, spacing=10)

    def load_records():
        records_list.controls.clear()
        query = search_input.value
        conn = sqlite3.connect('holy_communion.db')
        cursor = conn.cursor()
        if query:
            cursor.execute('''
                SELECT id, name, phone, address, minister_name, frequency, remarks 
                FROM registry WHERE name LIKE ? OR address LIKE ? ORDER BY id DESC
            ''', (f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('SELECT id, name, phone, address, minister_name, frequency, remarks FROM registry ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            records_list.controls.append(ft.Text("目前沒有登記資料。", color=ft.colors.GREY_500))
        else:
            for row in rows:
                record_id, record_name, record_phone, record_address = row[0], row[1], row[2], row[3]
                
                def call_phone(e, phone=record_phone):
                    if phone: page.launch_url(f"tel:{phone}")

                def open_whatsapp(e, phone=record_phone, name=record_name):
                    if phone:
                        clean_phone = phone.replace(" ", "").replace("-", "")
                        if not clean_phone.startswith("852"): clean_phone = f"852{clean_phone}"
                        msg = urllib.parse.quote(f"主內平安，{name}！我是堂區的聖體員，想和您確認這週送聖體的時間。")
                        page.launch_url(f"https://wa.me/{clean_phone}?text={msg}")

                def open_maps(e, address=record_address):
                    if address:
                        encoded_address = urllib.parse.quote(address)
                        page.launch_url(f"https://www.google.com/maps/search/?api=1&query={encoded_address}")

                def open_delete_dialog(e, r_id=record_id, r_name=record_name):
                    def confirm_delete(e):
                        db_conn = sqlite3.connect('holy_communion.db')
                        db_cursor = db_conn.cursor()
                        db_cursor.execute('DELETE FROM registry WHERE id = ?', (r_id,))
                        db_conn.commit()
                        db_conn.close()
                        page.dialog.open = False
                        page.snack_bar = ft.SnackBar(ft.Text(f"已刪除 {r_name} 的資料"), bgcolor=ft.colors.GREEN_600)
                        page.snack_bar.open = True
                        load_records()
                    def cancel_delete(e):
                        page.dialog.open = False
                        page.update()
                    confirm_dialog = ft.AlertDialog(
                        modal=True, title=ft.Text("確認刪除"),
                        content=ft.Text(f"確定要刪除教友「{r_name}」的登記資料嗎？此動作無法復原。"),
                        actions=[
                            ft.TextButton("取消", on_click=cancel_delete),
                            ft.TextButton("確認刪除", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED_600)),
                        ], actions_alignment=ft.MainAxisAlignment.END,
                    )
                    page.dialog = confirm_dialog
                    confirm_dialog.open = True
                    page.update()

                interactive_subtitle = ft.Column(
                    controls=[
                        ft.Row([
                            ft.TextButton("📞 撥號", on_click=call_phone, style=ft.ButtonStyle(padding=0, color=ft.colors.BLUE_700)),
                            ft.TextButton("💬 WhatsApp", on_click=open_whatsapp, style=ft.ButtonStyle(padding=0, color=ft.colors.GREEN_600)),
                        ], spacing=15, tight=True),
                        ft.TextButton(f"📍 地址: {record_address}", on_click=open_maps, style=ft.ButtonStyle(padding=0, color=ft.colors.BLUE_700)),
                        ft.Text(f"聖體員: {row[4]} ({row[5]})", color=ft.colors.GREY_700)
                    ], spacing=0, tight=True
                )
                
                delete_btn = ft.IconButton(icon=ft.icons.DELETE_OUTLINE, icon_color=ft.colors.RED_500, tooltip="刪除", on_click=open_delete_dialog)
                action_buttons = ft.Row(controls=[delete_btn], tight=True, spacing=0)

                records_list.controls.append(
                    ft.Card(content=ft.ListTile(leading=ft.Icon(ft.icons.PERSON_PIN), title=ft.Text(record_name, weight=ft.FontWeight.BOLD), subtitle=interactive_subtitle, trailing=action_buttons))
                )
        page.update()

    list_view = ft.Column(controls=[list_header, search_input, records_list], expand=True, visible=False)

    # --- [底部導覽切換邏輯] ---
    def nav_change(e):
        if e.control.selected_index == 0:
            form_view.visible = True
            list_view.visible = False
        else:
            form_view.visible = False
            list_view.visible = True
            load_records()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0, on_change=nav_change,
        destinations=[
            ft.NavigationDestination(icon=ft.icons.EDIT_DOCUMENT, label="新增登記"),
            ft.NavigationDestination(icon=ft.icons.FORMAT_LIST_BULLETED, label="瀏覽名單"),
        ]
    )
    load_records()
    page.add(form_view, list_view)

# 防止在 Android 環境中因為找不到 ft.app 導致崩潰
if hasattr(ft, "app"):
    ft.app(target=main)
