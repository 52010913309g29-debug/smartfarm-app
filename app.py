import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# ส่วนที่ 1: การตั้งค่าฐานข้อมูล
# ==========================================
DB_NAME = 'suansamrian_farm.db'

def run_query(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

def fetch_data(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Planting_Cycles
                     (Cycle_ID TEXT PRIMARY KEY, Zone_ID TEXT, Plant_Date DATE, Est_Harvest_Date DATE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Tasks
                     (Task_ID INTEGER PRIMARY KEY AUTOINCREMENT, Cycle_ID TEXT, Task_Name TEXT, Due_Date DATE, Status TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Expenses
                     (Exp_ID INTEGER PRIMARY KEY AUTOINCREMENT, Cycle_ID TEXT, Date DATE, Category TEXT, Amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Revenues
                     (Rev_ID INTEGER PRIMARY KEY AUTOINCREMENT, Cycle_ID TEXT, Date DATE, Quantity REAL, Amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS Sensor_Logs
                     (Log_ID INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp DATETIME, Sensor_Type TEXT, Value REAL)''')
        conn.commit()

init_db()

# ==========================================
# ส่วนหน้าจอแอปพลิเคชัน (Frontend & UI)
# ==========================================
st.set_page_config(page_title="Smart Farm Manager", layout="wide")
st.title("🌱 Smart Farm Manager - สวนบุญเสถียรประภาชัย")

st.sidebar.header("เมนูหลัก")
menu = ["1. จัดการการปลูก (Crop)", "2. ตารางงาน (Tasks)", "3. บัญชี (Finance)", "4. ข้อมูลเซ็นเซอร์ (IoT)", "5. จัดการข้อมูล (Edit Data)"]
choice = st.sidebar.radio("เลือกโมดูลการทำงาน:", menu)

# ==========================================
# โมดูลที่ 1 - 3 และ 5 (คงไว้ตามโครงสร้างเดิมที่เสถียรแล้ว)
# ==========================================
if choice == "1. จัดการการปลูก (Crop)":
    st.header("📋 โมดูลจัดการรอบการปลูก (Crop Management)")
    
    # ดึงข้อมูลรอบการปลูกทั้งหมดมาแสดงผลก่อน
    df_cycles = fetch_data("SELECT * FROM Planting_Cycles ORDER BY Plant_Date DESC")
    
    # แบ่งหน้าจอเป็น 3 แท็บ: เพิ่มข้อมูล, แก้ไขข้อมูล, และดูข้อมูลทั้งหมด
    tab_view, tab_add, tab_edit = st.tabs(["📊 ข้อมูลรอบการปลูกทั้งหมด", "➕ เพิ่มรอบการปลูกใหม่", "✏️ แก้ไขข้อมูลรอบการปลูก"])
    
    # --- แท็บที่ 1: ดูข้อมูลทั้งหมด ---
    with tab_view:
        st.subheader("ตารางแสดงรอบการปลูกปัจจุบัน")
        if not df_cycles.empty:
            st.dataframe(df_cycles, use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลรอบการปลูกในระบบ")

    # --- แท็บที่ 2: เพิ่มรอบการปลูกใหม่ (Create) ---
    with tab_add:
        with st.form("add_cycle_form"):
            st.subheader("กรอกรายละเอียดการปลูก")
            col1, col2 = st.columns(2)
            cycle_id = col1.text_input("รหัสรอบการปลูก (เช่น CYC-001)").strip()
            zone_id = col2.selectbox("เลือกล็อคแปลง", ["ล็อค A", "ล็อค B", "ล็อค C", "ล็อค D"])
            plant_date = st.date_input("วันที่ลงหัวพันธุ์")
            submitted = st.form_submit_button("บันทึกข้อมูล")
            
            if submitted:
                if not cycle_id: 
                    st.error("⚠️ กรุณากรอกรหัสรอบการปลูกก่อนบันทึก")
                else:
                    est_harvest = plant_date + timedelta(days=45) # คำนวณวันเก็บเกี่ยวอัตโนมัติ
                    try:
                        run_query("INSERT INTO Planting_Cycles (Cycle_ID, Zone_ID, Plant_Date, Est_Harvest_Date) VALUES (?, ?, ?, ?)", (cycle_id, zone_id, plant_date, est_harvest))
                        # สร้างงานพื้นฐานให้อัตโนมัติ
                        for i in range(1, 3):
                            run_query("INSERT INTO Tasks (Cycle_ID, Task_Name, Due_Date, Status) VALUES (?, ?, ?, 'รอดำเนินการ')", (cycle_id, "ฉีดพ่นไตรโคเดอร์มา", plant_date + timedelta(days=i*5)))
                        st.success(f"✅ บันทึกรอบปลูก {cycle_id} สำเร็จ!")
                        st.rerun()
                    except sqlite3.IntegrityError: 
                        st.error("⚠️ รหัสรอบการปลูกนี้มีอยู่แล้วในระบบ")

    # --- แท็บที่ 3: แก้ไขข้อมูลรอบการปลูก (Update) ---
    with tab_edit:
        st.subheader("แก้ไขรายละเอียดรอบการปลูก")
        if not df_cycles.empty:
            # ให้ผู้ใช้เลือกรหัสรอบการปลูกที่ต้องการแก้ไข
            selected_edit_id = st.selectbox("เลือกรหัสรอบการปลูกที่ต้องการแก้ไขข้อมูล:", df_cycles['Cycle_ID'].tolist())
            
            # ดึงข้อมูลเดิมของ ID นั้นมาแสดงสแตนบายไว้ในฟอร์ม
            row_data = df_cycles[df_cycles['Cycle_ID'] == selected_edit_id].iloc[0]
            
            with st.form("edit_cycle_form"):
                col1, col2 = st.columns(2)
                new_zone = col1.selectbox("เปลี่ยนล็อคแปลง", ["ล็อค A", "ล็อค B", "ล็อค C", "ล็อค D"], index=["ล็อค A", "ล็อค B", "ล็อค C", "ล็อค D"].index(row_data['Zone_ID']))
                new_plant_date = st.date_input("แก้ไขวันที่ลงหัวพันธุ์", value=pd.to_datetime(row_data['Plant_Date']).date())
                new_est_harvest = st.date_input("แก้ไขวันคาดการณ์เก็บเกี่ยว", value=pd.to_datetime(row_data['Est_Harvest_Date']).date())
                
                update_submitted = st.form_submit_button("💾 อัปเดตเปลี่ยนแปลงข้อมูล")
                if update_submitted:
                    run_query("UPDATE Planting_Cycles SET Zone_ID = ?, Plant_Date = ?, Est_Harvest_Date = ? WHERE Cycle_ID = ?", (new_zone, new_plant_date, new_est_harvest, selected_edit_id))
                    st.success(f"✏️ อัปเดตข้อมูลรอบปลูก {selected_edit_id} เรียบร้อยแล้ว!")
                    st.rerun()
        else:
            st.info("ไม่มีข้อมูลสำหรับการแก้ไข")
elif choice == "2. ตารางงาน (Tasks)":
    st.header("⏰ ตารางงานและระบบแจ้งเตือน")
    df_cycles = fetch_data("SELECT Cycle_ID FROM Planting_Cycles ORDER BY Plant_Date DESC")
    if not df_cycles.empty:
        selected_cycle = st.selectbox("เลือกรอบการปลูกเพื่อดูตารางงาน", df_cycles['Cycle_ID'].tolist())
        df_tasks = fetch_data("SELECT * FROM Tasks WHERE Cycle_ID = ? ORDER BY Due_Date", (selected_cycle,))
        if not df_tasks.empty:
            for index, row in df_tasks.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"📝 **{row['Task_Name']}** (ครบกำหนด: {row['Due_Date']})")
                if row['Status'] == 'รอดำเนินการ':
                    col2.warning("รอดำเนินการ")
                    if col3.button("✅ ทำเสร็จแล้ว", key=f"btn_{row['Task_ID']}"):
                        run_query("UPDATE Tasks SET Status = 'เสร็จแล้ว' WHERE Task_ID = ?", (row['Task_ID'],))
                        st.rerun()
                else: col2.success("เสร็จสิ้นแล้ว")
        else: st.info("ไม่มีงานสำหรับรอบการปลูกนี้")
    else: st.warning("ยังไม่มีข้อมูลรอบการปลูก")

elif choice == "3. บัญชี (Finance)":
    st.header("💰 บัญชีและวิเคราะห์การเงิน")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("expense_form"):
            st.subheader("🔴 บันทึกรายจ่าย")
            e_cycle = st.text_input("รหัสรอบปลูก").strip()
            e_cat = st.selectbox("หมวดหมู่", ["ค่าหัวพันธุ์", "ค่าปุ๋ย/ยา", "ค่าแรง", "ค่าน้ำมัน"])
            e_date = st.date_input("วันที่เกิดรายการ (รายจ่าย)")
            e_amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0)
            if st.form_submit_button("บันทึกรายจ่าย") and e_cycle and e_amount > 0:
                run_query("INSERT INTO Expenses (Cycle_ID, Date, Category, Amount) VALUES (?, ?, ?, ?)", (e_cycle, e_date, e_cat, e_amount))
                st.success("✅ บันทึกรายจ่ายสำเร็จ!")
    with col2:
        with st.form("revenue_form"):
            st.subheader("🟢 บันทึกรายรับ")
            r_cycle = st.text_input("รหัสรอบปลูกที่ขาย").strip()
            r_date = st.date_input("วันที่เกิดรายการ (รายรับ)")
            r_qty = st.number_input("น้ำหนักผลผลิต (กก.)", min_value=0.0)
            r_amount = st.number_input("ยอดเงินรวม (บาท)", min_value=0.0)
            if st.form_submit_button("บันทึกรายรับ") and r_cycle and r_amount > 0:
                run_query("INSERT INTO Revenues (Cycle_ID, Date, Quantity, Amount) VALUES (?, ?, ?, ?)", (r_cycle, r_date, r_qty, r_amount))
                st.success("✅ บันทึกรายรับสำเร็จ!")
    
    st.markdown("---")
    df_exp = fetch_data("SELECT SUM(Amount) as Total_Exp FROM Expenses")
    df_rev = fetch_data("SELECT SUM(Amount) as Total_Rev FROM Revenues")
    tot_exp = df_exp['Total_Exp'][0] if pd.notnull(df_exp['Total_Exp'][0]) else 0.0
    tot_rev = df_rev['Total_Rev'][0] if pd.notnull(df_rev['Total_Rev'][0]) else 0.0
    st.columns(3)[0].metric("รายรับรวม", f"฿ {tot_rev:,.2f}")
    st.columns(3)[1].metric("รายจ่ายรวม", f"฿ {tot_exp:,.2f}")
    st.columns(3)[2].metric("กำไรสุทธิ", f"฿ {(tot_rev - tot_exp):,.2f}", delta=(tot_rev - tot_exp))

# ==========================================
# [ปรับปรุงใหญ่] โมดูลที่ 4: ข้อมูลเซ็นเซอร์ (IoT Dashboard)
# ==========================================
elif choice == "4. ข้อมูลเซ็นเซอร์ (IoT)":
    st.header("📡 ศูนย์รวบรวมข้อมูลเซ็นเซอร์แปลงและบ่อเลี้ยง")
    st.markdown("ระบบวิเคราะห์และแสดงผลข้อมูลสภาพแวดล้อมทางกายภาพภายในฟาร์ม")
    
    # ส่วนจำลองการส่งข้อมูล (Hardware Simulator)
    with st.expander("🛠️ จำลองการส่งค่าจากฮาร์ดแวร์เซ็นเซอร์ (Wi-Fi)"):
        col1, col2, col3 = st.columns(3)
        sim_target = col1.selectbox("เลือกประเภทระบบ", ["ระบบดิน (Soil)", "ระบบน้ำ (Water)"])
        
        if sim_target == "ระบบดิน (Soil)":
            sensor_type = col2.selectbox("เลือกเซ็นเซอร์ดิน", ["ความชื้นในดิน (%)", "pH ของดิน", "ค่าปุ๋ยไนโตรเจน (N)"])
            sim_val = col3.number_input("ค่าที่วัดได้", min_value=0.0, max_value=100.0, value=50.0)
        else:
            sensor_type = col2.selectbox("เลือกเซ็นเซอร์น้ำ", ["pH ของน้ำ", "ออกซิเจนละลายน้ำ (DO)", "อุณหภูมิน้ำ (°C)"])
            sim_val = col3.number_input("ค่าที่วัดได้", min_value=0.0, max_value=50.0, value=7.0)
            
        if st.button("🚀 ส่งค่าเข้าฐานข้อมูลระบบ"):
            run_query("INSERT INTO Sensor_Logs (Timestamp, Sensor_Type, Value) VALUES (DATETIME('now', 'localtime'), ?, ?)", (sensor_type, sim_val))
            st.success(f"บันทึกค่า {sensor_type} = {sim_val} สำเร็จ!")
            st.rerun()

    st.markdown("---")
    
    # แยกแท็บการแสดงผลเพื่อให้เหมาะกับขนาดหน้าจอมือถือและคอมพิวเตอร์
    tab_soil, tab_water = st.tabs(["🌱 ระบบตรวจวัดค่าดิน (Soil Metrics)", "🐟 ระบบตรวจวัดค่าน้ำ (Water Metrics)"])
    
    # --- แท็บระบบดิน ---
    with tab_soil:
        st.subheader("การวิเคราะห์สภาพชั้นดิน")
        soil_sensor = st.selectbox("เลือกดูประวัติเซ็นเซอร์ดิน:", ["ความชื้นในดิน (%)", "pH ของดิน", "ค่าปุ๋ยไนโตรเจน (N)"])
        
        df_soil = fetch_data("SELECT Timestamp, Value FROM Sensor_Logs WHERE Sensor_Type = ? ORDER BY Timestamp DESC LIMIT 15", (soil_sensor,))
        
        if not df_soil.empty:
            df_soil['Timestamp'] = pd.to_datetime(df_soil['Timestamp'])
            df_soil.set_index('Timestamp', inplace=True)
            st.line_chart(df_soil)
            
            # ระบบประมวลผลและแจ้งเตือนอัจฉริยะ (Soil Rule-based Alert)
            latest_soil_val = df_soil['Value'].iloc[0]
            st.metric(f"ค่าปัจจุบันของ {soil_sensor}", f"{latest_soil_val:.2f}")
            
            if soil_sensor == "ความชื้นในดิน (%)":
                if latest_soil_val < 40: st.error("⚠️ แจ้งเตือน: ดินแห้งเกินไป ระบบสมควรเปิดระบบรดน้ำพ่นหมอก!")
                elif latest_soil_val > 80: st.warning("⚠️ แจ้งเตือน: ดินแฉะเกินไป ระวังระบบรากเน่าและเชื้อรา!")
                else: st.success("✅ ความชื้นในดินอยู่ในเกณฑ์เหมาะสมกับการเจริญเติบโต")
            elif soil_sensor == "pH ของดิน":
                if latest_soil_val < 5.5: st.error("⚠️ แจ้งเตือน: ดินเป็นกรดจัด (ดินเปรี้ยว) แนะนำให้เติมปูนขาวปรับสภาพ")
                elif latest_soil_val > 7.0: st.warning("⚠️ แจ้งเตือน: ดินเป็นด่าง เกรงว่าพืชจะดูดซึมธาตุอาหารได้ยาก")
                else: st.success("✅ ค่าความเป็นกรด-ด่างของดินเป็นกลาง เหมาะสมดีเยี่ยม")
        else:
            st.info("ยังไม่มีข้อมูลบันทึกจากเซ็นเซอร์ดินประเภทนี้")

    # --- แท็บระบบน้ำ ---
    with tab_water:
        st.subheader("การวิเคราะห์คุณภาพน้ำ")
        water_sensor = st.selectbox("เลือกดูประวัติเซ็นเซอร์น้ำ:", ["pH ของน้ำ", "ออกซิเจนละลายน้ำ (DO)", "อุณหภูมิน้ำ (°C)"])
        
        df_water = fetch_data("SELECT Timestamp, Value FROM Sensor_Logs WHERE Sensor_Type = ? ORDER BY Timestamp DESC LIMIT 15", (water_sensor,))
        
        if not df_water.empty:
            df_water['Timestamp'] = pd.to_datetime(df_water['Timestamp'])
            df_water.set_index('Timestamp', inplace=True)
            st.line_chart(df_water)
            
            # ระบบประมวลผลและแจ้งเตือนอัจฉริยะ (Water Rule-based Alert)
            latest_water_val = df_water['Value'].iloc[0]
            st.metric(f"ค่าปัจจุบันของ {water_sensor}", f"{latest_water_val:.2f}")
            
            if water_sensor == "ออกซิเจนละลายน้ำ (DO)":
                if latest_water_val < 4.0: st.error("🚨 วิกฤต: ค่า DO ต่ำกว่ามาตรฐาน! ปลาอาจขาดอากาศหายใจ เปิดเครื่องตีน้ำด่วน!")
                else: st.success("✅ ปริมาณออกซิเจนในน้ำเพียงพอและปลอดภัยต่อสัตว์น้ำ")
            elif water_sensor == "pH ของน้ำ":
                if latest_water_val < 6.5 or latest_water_val > 8.5: st.error("⚠️ แจ้งเตือน: คุณภาพน้ำไม่อยู่ในเกณฑ์ปลอดภัยสำหรับเลี้ยงปลา")
                else: st.success("✅ ค่า pH ของน้ำอยู่ในเกณฑ์สมดุล")
        else:
            st.info("ยังไม่มีข้อมูลบันทึกจากเซ็นเซอร์น้ำประเภทนี้")

elif choice == "5. จัดการข้อมูล (Edit Data)":
    st.header("⚙️ ระบบหลังบ้าน - ลบข้อมูลที่กรอกผิดพลาด")
    
    tab_del_crop, tab_del_finance = st.tabs(["🌱 ลบรอบการปลูก", "💰 ลบบัญชีรายรับ-รายจ่าย"])
    
    # --- แท็บลบรอบการปลูก (Delete) ---
    with tab_del_crop:
        st.subheader("🗑️ ลบข้อมูลรอบการปลูก (Cascading Delete)")
        st.warning("⚠️ คำเตือน: การลบรอบการปลูก จะลบข้อมูลตารางงาน บัญชี และค่าเซ็นเซอร์ที่ผูกอยู่กับรหัสรอบปลูกนี้ออกทั้งหมด!")
        
        df_cycles = fetch_data("SELECT * FROM Planting_Cycles ORDER BY Plant_Date DESC")
        if not df_cycles.empty:
            st.dataframe(df_cycles, use_container_width=True)
            del_cycle_id = st.selectbox("เลือกรหัสรอบการปลูกที่ต้องการลบทิ้งถาวร:", ["-- เลือกใบงาน --"] + df_cycles['Cycle_ID'].tolist())
            
            if st.button("🚨 ยืนยันการลบข้อมูลถาวร") and del_cycle_id != "-- เลือกใบงาน --":
                # ลบข้อมูลในตารางหลัก
                run_query("DELETE FROM Planting_Cycles WHERE Cycle_ID = ?", (del_cycle_id,))
                # ลบข้อมูลตารางอื่นที่เกี่ยวข้องกันเพื่อไม่ให้ฐานข้อมูลขยะค้าง
                run_query("DELETE FROM Tasks WHERE Cycle_ID = ?", (del_cycle_id,))
                run_query("DELETE FROM Expenses WHERE Cycle_ID = ?", (del_cycle_id,))
                run_query("DELETE FROM Revenues WHERE Cycle_ID = ?", (del_cycle_id,))
                
                st.success(f"🗑️ ลบข้อมูลรอบปลูก {del_cycle_id} และงานที่เกี่ยวข้องเรียบร้อยแล้ว!")
                st.rerun()
        else:
            st.info("ไม่มีข้อมูลรอบการปลูกให้ลบ")

    # --- แท็บบัญชีเดิม ---
    with tab_del_finance:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("ตารางรายจ่าย")
            st.dataframe(fetch_data("SELECT * FROM Expenses ORDER BY Exp_ID DESC"), use_container_width=True)
            del_exp = st.number_input("พิมพ์รหัส Exp_ID ที่ต้องการลบ", min_value=0, step=1)
            if st.button("🗑️ ลบรายการรายจ่าย") and del_exp > 0:
                run_query("DELETE FROM Expenses WHERE Exp_ID = ?", (del_exp,))
                st.success("ลบรายการสำเร็จ"); st.rerun()
        with col2:
            st.subheader("ตารางรายรับ")
            st.dataframe(fetch_data("SELECT * FROM Revenues ORDER BY Rev_ID DESC"), use_container_width=True)
            del_rev = st.number_input("พิมพ์รหัส Rev_ID ที่ต้องการลบ", min_value=0, step=1)
            if st.button("🗑️ ลบรายการรายรับ") and del_rev > 0:
                run_query("DELETE FROM Revenues WHERE Rev_ID = ?", (del_rev,))
                st.success("ลบรายการสำเร็จ"); st.rerun()
