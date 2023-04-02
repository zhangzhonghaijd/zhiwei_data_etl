import pandas as pd
import os
from datetime import date
import warnings
warnings.filterwarnings('ignore')
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
from multi_pages import MultiPages
import streamlit as st
import numpy as np
# import graphviz
from datetime import date,datetime

st.set_page_config(
    page_title="知微可视化看板",
    page_icon="********",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)




DailyBusiness = "日常事务"
UserStory = "用户故事"
TimeList = "工时列表"
StaffInformation = "参与成员"
ProjectResource = "项目资源"

@st.cache()
def get_path(path, Date):
    '''
    得到改路径下的指定日期的文件
    :param path: 路径
    :param Date: 日期，时间格式
    :return:
    '''
    for dir_name in os.listdir(path):
        if dir_name.find(Date.strftime("%Y-%m-%d")) >= 0:
            return os.path.join(path, dir_name)
    return None


def read_data(path, flag_word):
    '''
    找到指定路径下的文件
    :param path:
    :param flag_word: 文件包含的标识文字
    :return:
    '''
    for name in os.listdir(path):
        if name.find(flag_word) >= 0:
            data = pd.read_excel(os.path.join(path, name))
            data.columns = data.columns.map(lambda x: x.split('(')[0])
            return data
    return None
@st.cache()
def preprocess_daily_business(path,flag_word):
    '''
    日常事务预处理
    :param path:
    :param flag_word:
    :return:
    '''
    # 删除日常事务表无意义列
    data = read_data(path=path,flag_word=flag_word)
    #删除空字段
    data.drop(['丢弃时间','丢弃原因','还原原因','归档时间','标签','丢弃人','归档人',
               '关注的成员','容器','卡片类型'],axis=1,inplace=True)
    us_key_str = "负责人"
    data.dropna(subset=[us_key_str], inplace=True)
    #拆分负责人
    data[us_key_str] = data[us_key_str].str.split(',')
    data = data.explode(us_key_str)
    # 删除已完成日常事务
    # data = data[data["状态"] != "已完成"]
    return data

@st.cache()
def preprocess_user_story(path,flag_word):
    '''
    用户故事预处理
    :param path:
    :param flag_word:
    :return:
    '''
    # #删除用户故事表无意义列
    data = read_data(path=path, flag_word=flag_word)
    data.drop(['丢弃时间','丢弃原因','还原原因','归档时间','标签','丢弃人','归档人',
               '关注的成员', '容器', '卡片类型'], axis=1, inplace=True)
    # 关键词：负责人(关联关系)、'创建人(关联关系)'
    # 存在创建人和负责人都为空的现象，这里认为如果事务创建但没有负责人，则怀疑1、是事务阻/取消/未开始,导致没人认领；2、忘了指定负责人
    # 将负责人为空的数据删除，
    db_key_str = "负责人"
    data.dropna(subset=[db_key_str], inplace=True)
    #拆分负责人
    data[db_key_str] = data[db_key_str].str.split(',')
    data = data.explode(db_key_str)
    data["状态"] = data["状态"].map(lambda x:x.split('-')[0])
    #删除已完成用户故事
    # data = data[data["状态"]!="已完成"]

    return data

def preprocess_time_list(path,flag_word):
    '''
    工时列表预处理
    :param path:
    :param flag_word:
    :return:
    '''
    data = read_data(path=path, flag_word=flag_word)
    #删除工时列表无意义列
    data.drop(["记录名称","描述","描述"], axis=1, inplace=True)
    data['工作日期'] = pd.to_datetime(data['工作日期']).dt.date
    data = data[data["工时（小时）"]!=0]
    return data
@st.cache()
def preprocess_staff_information(path,flag_word):
    '''
    参与成员预处理
    :param path:
    :param flag_word:
    :return:
    '''
    data = read_data(path=path, flag_word=flag_word)[["公司部门-部门","姓名","角色"]]
    data.rename(columns = {"公司部门-部门":"部门","角色":"岗位"})
    data.drop_duplicates(inplace=True)
    return data

@st.cache()
def preprocess_project_resource(path,flag_word):
    '''
    项目资源预处理
    :param path:
    :param flag_word:
    :return:
    '''
    data = read_data(path=path,flag_word=flag_word)
    #删除虚拟项目
    data = data[~data["标题"].str.contains("虚拟项目")]
    data = data[['标题', '创建时间', '状态','投入百分比','创建人',
    '实际开始日期', '项目成员', '计划开始日期','计划完成日期']]
    #项目名称
    data["项目名称"]= data["标题"].map(lambda x:x.split("-")[0])
    #删除已经完成的项目
    drop_values = []
    for item in data[["项目名称", "状态"]].values:
        if item[1]!="已退场":
            drop_values.append(item[0])
    data = data[data["项目名称"].isin(set(drop_values))]
    #获取人员角色
    data["角色"] = data["标题"].map(lambda x: x.split("-")[1])
    #项目罗塞塔项目名称
    data["项目名称"] = data["项目名称"].map(lambda x: "罗塞塔可视化" if x=='rst' else x)
    #投入百分比
    data["投入百分比"] = data["投入百分比"].map(lambda x: "{:.0%}".format(x) if x==x else '')
    return data


# data.columns = data.columns.map(lambda x: flag_word + "_" + x)
@st.cache()
def get_employee_data(path, Date):
    # 全体员工信息
    # staff_key_str = StaffInformation + "_" + "姓名"
    # data_staff = preprocess_staff_information(path, StaffInformation)
    # 用户故事看板
    data_DB = preprocess_daily_business(path, DailyBusiness)
    # df = pd.merge(data_staff, data_DB, left_on=staff_key_str,
    #               right_on=db_key_str, how="left")
    # 日常事务看板
    data_US = preprocess_user_story(path, UserStory)
    # df = pd.merge(df, data_US, left_on=staff_key_str,
    #               right_on=us_key_str, how="left")
    # 工时列表
    # tl_key_str = TimeList + "_" + "成员"
    # data_TL = read_data(file_path, TimeList)
    # df = pd.merge(df, data_TL, left_on=staff_key_str,
    #               right_on=tl_key_str, how="left")

    return data_DB,data_US


def kanban_project_resource(path = r'./dataSet/2023-03-15'):
    """
    """
    """
    *********
    注：该页所展示项目为待开发或正在交付中的项目。
    *********
    """
    project_resources_df = preprocess_project_resource(path,flag_word="资源管理")
    # 人员数
    """
    ### 项目人员分布视图
    """
    chart_data = project_resources_df.pivot_table(index="项目名称", columns="状态", values="角色", aggfunc='count')
    chart_data.fillna(0,inplace=True)
    st.bar_chart(chart_data,use_container_width = True)
    """
    *********
    ### 项目人员分布明细
    """
    # 项目人员情况 -table明细
    col1, col2= st.columns(2)
    option_1 = col1.selectbox(
        '项目名称：',
        project_resources_df["项目名称"].unique())
    option_2 = col2.selectbox(
        '人员交付状态：',
        np.append(np.array(["全部"]),project_resources_df["状态"].unique()))
    if option_2 == "全部":
        select_df = project_resources_df[(project_resources_df["项目名称"]==option_1)]
    else:
        select_df = project_resources_df[(project_resources_df["项目名称"]==option_1)&
                                          (project_resources_df["状态"]==option_2)]
    select_df = select_df[["创建人","项目成员","角色","状态","投入百分比","计划开始日期","计划完成日期"]]
    select_df.rename(columns={'创建人': '项目负责人'}, inplace=True)
    st.dataframe(select_df)

    #项目负责人
    # project_person = project_resources_df[["创建人","项目名称"]].drop_duplicates()
    # st.dataframe(project_person)

    # graph = graphviz.Digraph()
    # for index,row in project_person.iterrows():
    #     graph.edge(row["创建人"], row["项目名称"])

    # st.graphviz_chart(graph)
    # st.dataframe(project_resources_df.iloc[:,0])
    # col1, col2, col3 = st.columns(3)
    # col1.metric("项目数", "70 °F", "1.2 °F")
    # col2.metric("故事数", "9 mph", "-8%")
    # col3.metric("事务数", "86%", "4%")



def get_employee_works(path):
    db_data, us_data = get_employee_data(path, Date)
    staff_df = preprocess_staff_information(path, StaffInformation)
    """
    *********
    ### 日常事务明细
    *********
    """
    st.dataframe(db_data)
    agg_db = db_data.pivot_table(index="负责人", columns="状态", values="ID", aggfunc='count')
    # 增加/删除行
    add_persons = set(staff_df["姓名"].values) - set(agg_db.index)
    drop_persons = set(agg_db.index) - set(staff_df["姓名"].values)
    agg_db = pd.concat([agg_db, pd.DataFrame(index=add_persons, columns=agg_db.columns)], axis=0).fillna(0)
    agg_db.drop(drop_persons, axis=0, inplace=True)
    # 排序取整，合计
    agg_db = agg_db[["待办", "进行中", "已完成"]].applymap(lambda x: int(x))
    agg_db.insert(0, "合计", agg_db.sum(axis=1))
    # agg_db.columns = pd.MultiIndex.from_product([["日常事务"],agg_db.columns])
    # st.write(db_data.shape)
    """
    *********
    ### 用户故事明细
    *********
    """
    st.dataframe(us_data)
    agg_us = us_data.pivot_table(index="负责人", columns="状态", values="ID", aggfunc='count')
    # 增加/删除行
    add_persons = set(staff_df["姓名"].values) - set(agg_us.index)
    drop_persons = set(agg_us.index) - set(staff_df["姓名"].values)
    agg_us = pd.concat([agg_us, pd.DataFrame(index=add_persons, columns=agg_us.columns)], axis=0).fillna(0)
    agg_us.drop(drop_persons, axis=0, inplace=True)
    # 排序取整，合计
    agg_us = agg_us[["故事池", "需求澄清", "就绪", "开发中", "测试中", "待上线", "已上线"]].applymap(lambda x: int(x))
    agg_us.insert(0, "合计", agg_us.sum(axis=1))
    """
    *********
    ### 员工日常事务&故事计数
    *********
    """
    option = st.selectbox(
        '请选择员工：',
        np.append(np.array(["全部"]), staff_df['姓名'].values))
    col1, col2 = st.columns([3, 5])
    col1.write("日常事务情况：")
    col2.write("用户故事情况：")
    if option == "全部":
        col1.dataframe(agg_db)
        col2.dataframe(agg_us)
    else:
        col1.dataframe(agg_db.loc[[option], :])
        col2.dataframe(agg_us.loc[[option], :])

def kanban_employee_business(path = r'./dataSet/2023-03-15'):
    #信息整合
    get_summary_data(path=path)
    #事故/故事详细列表
    get_employee_works(path=path)
    #在制品情况/工作量
    get_employee_workload(path=path)


def get_employee_workload(path):
    """
    1.暴露当前日期无员工工时的
    2.员工工作量日趋图
    3.员工工作量排名
    """
    data = preprocess_time_list(path=path,flag_word=TimeList)
    data["工时（小时）"] = data["工时（小时）"].map(lambda x:int(x))
    staff_df = preprocess_staff_information(path, StaffInformation)
    #原始数据
    # 项目人员情况 -table明细
    """
    ### 员工工作明细
    """
    col1, col2= st.columns(2)
    option_1 = col1.selectbox(
        '工作日期：',
        np.append(np.array(["全部"]),data["工作日期"].unique()))
    option_2 = col2.selectbox(
        '员工：',
        np.append(np.array(["全部"]),data["成员"].unique()))
    if option_1 == "全部":
        if option_2=="全部":
            st.dataframe(data[["成员","工时（小时）","所属项目","工作的任务"]])
        else:
            st.dataframe(data[data["成员"]==option_2][["成员","工时（小时）","所属项目","工作的任务"]])
    else:
        if option_2=="全部":
            st.dataframe(data[data["工作日期"]==option_1][["成员","工时（小时）","所属项目","工作的任务"]])
        else:
            st.dataframe(data[(data["成员"]==option_2)&(data["工作日期"]==option_1)][["成员","工时（小时）","所属项目","工作的任务"]])
    """
    *********
    """
    plt_data = data.pivot_table(index = "成员",columns = "工作日期",values = "工作的任务",aggfunc="count")
    plt_data = plt_data[plt_data.index.isin(staff_df["姓名"].values)]
    plt_data = plt_data.fillna(0).applymap(lambda x:int(x))
    # plt_data.columns = plt_data.columns.map(lambda x:trans_str_date(x))
    # 在制品个数
    # st.dataframe(plt_data)
    """
    ### 员工在制品个数序列
    """
    option_1 = st.selectbox(
        '员工姓名：',
        plt_data.index)
    now_date = date(datetime.now().year,datetime.now().month,datetime.now().day)
    values = st.slider(
        '请筛选日期：',
        date(2021,1,31),now_date,[date(2022,1,31),now_date])
    st.line_chart(plt_data.loc[option_1,values[0]:values[1]])
    """
    *********
    """

def get_summary_data(path):
    staff_df = preprocess_staff_information(path, StaffInformation)
    staff_df = staff_df.rename(columns={"公司部门-部门": "部门"})
    project_df = preprocess_project_resource(path,ProjectResource)
    project_df = project_df[project_df["状态"]=="交付中"][["项目成员","项目名称","投入百分比"]]
    # 所属项目
    suxm_df = project_df.groupby(["项目成员"])["项目名称"].apply(list).to_frame().reset_index()
    suxm_df = suxm_df.rename(columns = {"项目成员":"姓名","项目名称":"参与项目"})
    df1 = pd.merge(left=staff_df, right=suxm_df, how="left", left_on="姓名", right_on="姓名")
    df1.fillna('',inplace=True)
    # 参与项目数量
    cyxmsl_df = project_df.groupby(["项目成员"])["项目名称"].count().reset_index()
    cyxmsl_df = cyxmsl_df.rename(columns={"项目成员": "姓名", "项目名称": "参与项目数量"})
    df2 = pd.merge(left=df1, right=cyxmsl_df, how="left", left_on="姓名", right_on="姓名")
    df2.fillna(0, inplace=True)
    # 日常事务看板
    data_DB = preprocess_daily_business(path, DailyBusiness)
    # 用户故事看板
    data_US = preprocess_user_story(path, UserStory)
    data_DB = data_DB[data_DB["状态"]=="进行中"][["标题","所属项目","负责人"]]
    data_US = data_US[data_US["状态"]!="已上线"][["标题","所属项目","负责人"]]
    data_db_us = pd.concat([data_DB,data_US],axis=0)
    #负责故事和事务名称
    fzgsmc_df = data_db_us.groupby(["负责人"])["所属项目"].apply(list).to_frame().reset_index()
    fzgsmc_df = fzgsmc_df.rename(columns={"负责人": "姓名", "所属项目": "负责事务名称"})
    df3 = pd.merge(left=df2, right=fzgsmc_df, how="left", left_on="姓名", right_on="姓名")
    df3.fillna('', inplace=True)
    #负责故事和事务数量
    gsswsl_df = data_db_us.groupby(["负责人"])["标题"].count().reset_index()
    gsswsl_df = gsswsl_df.rename(columns={"负责人": "姓名", "标题": "负责故事/事务数量"})
    df4 = pd.merge(left=df3, right=gsswsl_df, how="left", left_on="姓名", right_on="姓名")
    df4.fillna('', inplace=True)
    #当天在制品数量
    df4["当天在制品数量"] = 0
    #本周平均在制品数量
    df4["本周平均在制品数量"] = 0
    option_1 = st.selectbox(
        '员工姓名：',
        df4["姓名"].values)
    select_df4 = df4[df4["姓名"]==option_1]
    st.dataframe(select_df4)

if __name__ == '__main__':
    Date = date(2023, 3, 15)
    # get_summary_data(path=r'./dataSet/2023-03-15')
    app = MultiPages()
    app.add_app("项目资源情况", kanban_project_resource)
    app.add_app("员工工作情况", kanban_employee_business)
    # app.add_app("员工工时情况",kanban_employee_works)
    app.run()
    # data = get_data(r'./dataSet', Date)
