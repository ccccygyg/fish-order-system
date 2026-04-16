from nicegui import ui
import requests
import base64
from PIL import Image
import io

# --- 1. 基本設定 ---
# 請記得換成你最新的部署網址
SCRIPT_URL = "你的最新GAS網址"

def process_image(content):
    img = Image.open(io.BytesIO(content))
    img.thumbnail((500, 500))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode()

# --- 2. 狀態管理 ---
# 用一個字典來記錄當前顧客點的數量，以便即時顯示總額
cart = {}

# --- 3. 介面設計 ---
@ui.page('/')
def main_page():
    ui.colors(primary='#1976d2', secondary='#26a69a', accent='#ef5350')

    # 左側導覽列
    with ui.left_drawer().style('background-color: #f8f9fa'):
        ui.label('🐟 金富水產系統').classes('text-2xl font-black mb-4 text-blue-800')
        menu = ui.radio(['🐟 顧客點貨單', '⚙️ 老闆管理後台'], value='🐟 顧客點貨單').classes('w-full')

    # 右側主要內容區
    container = ui.column().classes('w-full items-center')

    # ----------------------------
    # 頁面 1：顧客點貨單
    # ----------------------------
    with container.bind_visibility_from(menu, 'value', value='🐟 顧客點貨單').classes('w-full max-w-4xl p-4'):
        ui.label('今日漁獲').classes('text-3xl font-black mb-2')
        ui.label('請選擇漁獲並填寫資料，點擊下方送出即可完成預訂。').classes('text-gray-500 mb-6')

        @ui.refreshable
        def product_grid():
            try:
                # 取得產品資料
                response = requests.get(f"{SCRIPT_URL}?action=getProducts", timeout=10)
                fishes = response.json()
                
                # 總額顯示 (即時刷新用)
                total_label = ui.label('目前總計：$0').classes('text-2xl font-black text-red-600 mb-4')

                def update_total():
                    current_total = sum(item['price'] * item['qty'] for item in cart.values())
                    total_label.set_text(f'目前總計：${current_total:.0f}')

                with ui.grid(columns=ui.breakpoint('sm', 1).breakpoint('md', 3)).classes('w-full gap-6'):
                    for fish in fishes:
                        with ui.card().tight().classes('rounded-xl shadow-md overflow-hidden'):
                            if fish.get('img'):
                                ui.image(f"data:image/jpeg;base64,{fish['img']}").classes('h-48 w-full object-cover')
                            
                            with ui.column().classes('p-4 w-full'):
                                ui.label(fish['name']).classes('text-xl font-bold')
                                ui.label(f"單價：${fish['price']}").classes('text-red-500 font-medium')
                                
                                stock = int(fish.get('stock', 0))
                                if stock <= 0:
                                    ui.label('❌ 已完售').classes('text-gray-400 py-2')
                                else:
                                    ui.label(f'✅ 庫存：{stock}').classes('text-green-600 text-sm')
                                    def on_qty_change(e, f=fish):
                                        if e.value > 0:
                                            cart[f['name']] = {'qty': e.value, 'price': f['price']}
                                        elif f['name'] in cart:
                                            del cart[f['name']]
                                        update_total()

                                    ui.number(label='預訂數量', value=0, min=0, max=stock, step=1, 
                                              on_change=on_qty_change).classes('w-full mt-2')

                # 結帳表單
                with ui.card().classes('w-full mt-10 bg-blue-50 p-6 rounded-2xl border-2 border-blue-100 shadow-inner'):
                    ui.label('📝 訂購人資訊').classes('text-2xl font-bold mb-4')
                    name_in = ui.input('姓名').classes('w-full mb-2').props('outlined')
                    phone_in = ui.input('手機電話').classes('w-full mb-2').props('outlined')
                    note_in = ui.input('備註 (如：魚要切、去鱗)').classes('w-full mb-4').props('outlined')
                    
                    async def handle_submit():
                        if not cart:
                            ui.notify('請先選擇漁獲數量！', type='warning')
                            return
                        if not name_in.value or not phone_in.value:
                            ui.notify('請填寫姓名與電話', type='warning')
                            return
                        
                        items_str = ", ".join([f"{k}x{v['qty']}" for k, v in cart.items()])
                        payload = {
                            "name": name_in.value,
                            "phone": phone_in.value,
                            "items": items_str,
                            "note": note_in.value
                        }
                        
                        with ui.spinner(size='lg'):
                            # 執行 POST 請求
                            requests.post(SCRIPT_URL, data=payload)
                            
                        ui.notify('🎉 訂單送出成功！我們會盡快為您預留。', type='positive', position='top')
                        cart.clear()
                        ui.open('/') # 重刷頁面

                    ui.button('🚀 點我確認送出訂單', on_click=handle_submit).classes('w-full py-6 text-xl font-bold rounded-xl shadow-lg')
            except Exception as e:
                ui.label(f'連線異常：{e}').classes('text-red-500 text-center mt-10')
        
        product_grid()

    # ----------------------------
    # 頁面 2：老闆管理後台
    # ----------------------------
    with container.bind_visibility_from(menu, 'value', value='⚙️ 老闆管理後台').classes('w-full max-w-4xl p-4'):
        password = ui.input('管理員登入', password=True).classes('w-full mb-6').props('outlined rounded')
        
        with ui.column().bind_visibility_from(password, 'value', value='8888').classes('w-full'):
            with ui.tabs().classes('w-full shadow-md rounded-lg') as tabs:
                tab1 = ui.tab('🆕 快速上架')
                tab2 = ui.tab('📦 庫存管理')
                tab3 = ui.tab('📋 訂單交貨')

            with ui.tab_panels(tabs, value=tab3).classes('w-full bg-transparent'):
                # --- Tab 1: 上架 ---
                with ui.tab_panel(tab1):
                    with ui.card().classes('p-6'):
                        p_name = ui.input('漁獲名稱').classes('w-full mb-2')
                        p_price = ui.number('單價', value=0, min=0).classes('w-full mb-2')
                        p_stock = ui.number('進貨數量', value=1, min=1).classes('w-full mb-2')
                        # 檔案上傳
                        p_file = ui.upload(label='📷 拍照或選取照片', on_upload=lambda e: setattr(p_file, 'content', e.content)).classes('w-full mb-4')
                        
                        async def add_product():
                            if not p_name.value or not hasattr(p_file, 'content'):
                                ui.notify('請填寫名稱並上傳照片', type='warning')
                                return
                            with ui.spinner():
                                img_b64 = process_image(p_file.content)
                                requests.post(SCRIPT_URL, data={
                                    "action": "addProduct",
                                    "name": p_name.value,
                                    "price": p_price.value,
                                    "stock": p_stock.value,
                                    "imgData": img_b64
                                })
                            ui.notify('✅ 商品已上架同步至雲端', type='positive')
                            p_name.set_value(''); p_file.reset()

                        ui.button('立即同步上架', on_click=add_product).classes('w-full py-4 text-lg font-bold')

                # --- Tab 2: 庫存 ---
                with ui.tab_panel(tab2):
                    @ui.refreshable
                    def stock_list():
                        p_data = requests.get(f"{SCRIPT_URL}?action=getProducts").json()
                        for f in p_data:
                            with ui.row().classes('w-full items-center justify-between border-b py-3'):
                                with ui.column():
                                    ui.label(f['name']).classes('text-lg font-bold')
                                    ui.label(f"剩餘數量: {f['stock']} | 售價: ${f['price']}").classes('text-gray-500 text-sm')
                                
                                def delete_p(name=f['name']):
                                    requests.get(f"{SCRIPT_URL}?action=deleteProduct&name={name}")
                                    ui.notify(f'{name} 已從列表移除')
                                    stock_list.refresh()

                                ui.button('下架', color='red', on_click=delete_p).props('flat')
                    
                    stock_list()

                # --- Tab 3: 訂單 (局部刷新) ---
                with ui.tab_panel(tab3):
                    @ui.refreshable
                    def orders_ui():
                        raw_orders = requests.get(f"{SCRIPT_URL}?action=getOrders").json()
                        if not raw_orders:
                            ui.label('目前沒有新訂單').classes('text-gray-400 text-center w-full mt-10')
                            return

                        grouped = {}
                        for o in raw_orders:
                            oid = o.get('orderId', 'Old')
                            if oid not in grouped: grouped[oid] = []
                            grouped[oid].append(o)

                        for oid, items in grouped.items():
                            first = items[0]
                            with ui.expansion(f"👤 {first['name']} - 總額: ${sum(float(i['total']) for i in items):.0f}").classes('w-full border rounded-lg mb-4 shadow-sm'):
                                with ui.column().classes('p-4 w-full bg-white'):
                                    ui.label(f"📞 電話：{first['phone']}").classes('font-bold')
                                    if first['note']:
                                        ui.label(f"📝 備註：{first['note']}").classes('text-orange-600 bg-orange-50 p-2 rounded')
                                    
                                    ui.separator().classes('my-2')
                                    
                                    for item in items:
                                        with ui.row().classes('w-full justify-between py-1'):
                                            ui.label(f"🔹 {item['item']}")
                                            ui.label(f"${item['total']}").classes('font-bold')
                                    
                                    # 交貨與抽離按鈕區
                                    with ui.row().classes('w-full mt-4 gap-2'):
                                        async def deliver(o_id=oid):
                                            with ui.spinner():
                                                requests.get(f"{SCRIPT_URL}?action=deleteGroup&orderId={o_id}")
                                            ui.notify('✅ 訂單交貨完成')
                                            orders_ui.refresh()
                                        
                                        ui.button('🚀 整單完成交貨', color='green', on_click=deliver).classes('flex-grow py-3 rounded-xl font-black')
                                        
                    ui.button('🔄 刷新訂單狀態', on_click=orders_ui.refresh).classes('w-full mb-6 py-3 shadow-md').props('icon=refresh')
                    orders_ui()

ui.run(title="金富水產系統", port=8080, reload=True)