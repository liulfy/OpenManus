


import pandas as pd

file_name = "users_chinatelecom.cn_260313.xlsx"
df = pd.read_excel(file_name, engine="openpyxl")
data_size = len(df)

result = []

for i in range(data_size):
    row_data = df.iloc[i]
    city_num = row_data["地市区号"]
    city = row_data["地市名"]
    name = row_data["姓名"]
    zhanghaobianma = row_data["员工号编码"]
    dianhuahaoma = row_data["手机号"]
    this_result = f"20260311^-1^D3A758D49D2C44BA888F30722EE427E2^RAG知识管理平台^{city_num}^{city}^{name}^{zhanghaobianma}^-1^-1^-1^{dianhuahaoma}^1^0^0^user_role^普通用户^priv_user^受理权限^省智能云网业务运营中心^数据和AI支撑部\n"
    result.append(this_result)



with open('system_staff_account_role_info_iboc_zsgc_20260311.txt', 'w', encoding='utf-8') as f:
    f.writelines(result)  # writelines 接收字符串列表，不会自动加换行符，需手动加





import pandas as pd

# 读取两个Excel文件
# 读取导出.xlsx文件，获取姓名列
df_export = pd.read_excel('导出.xlsx')
# 读取IBOC新增点将台人员.xlsx文件，获取支撑人列
df_new = pd.read_excel('IBOC新增点将台人员.xlsx')

names = set()
export_size = len(df_export)
new_size = len(df_new)
for i in range(export_size):
    name = df_export.iloc[i]['姓名']
    names.add(name)

for i in range(new_size):
    name = df_new.iloc[i]['支撑人']
    if not name in names:
        print(name)
        print(i+2)


# 查看导出.xlsx文件的列名，确认姓名列的具体名称
print("导出.xlsx文件的列名：")
print(df_export.columns.tolist())
print("\n导出.xlsx文件的前5行数据：")
print(df_export.head())
print(f"\n导出.xlsx文件共有 {len(df_export)} 行数据")

print("\n" + "="*50 + "\n")

# 查看IBOC新增点将台人员.xlsx文件的列名，确认支撑人列的具体名称
print("IBOC新增点将台人员.xlsx文件的列名：")
print(df_new.columns.tolist())
print("\nIBOC新增点将台人员.xlsx文件的前5行数据：")
print(df_new.head())
print(f"\nIBOC新增点将台人员.xlsx文件共有 {len(df_new)} 行数据")


