from flask import render_template
from app.config import MODULES,TITLE,SHORT
from app.pipeline import execute,load_sample
from app import store
def register_pages(app):
    def page(index):
        run=store.latest() or execute(load_sample("dirty.csv"))
        stage=run["stages"][index]
        rows=stage["rows"]
        choices=[['event_id','card','route','event_time','result','reported','ticket_type'],['event_id','card','route','line_group'],['event_id','card','fare_version','ticket_type','base_fare','payable_fare','reported','at'],['journey','card','route','business_day','at'],['event_id','card','route','ticket_type','base_fare','payable_fare','transfer_entitlement','transfer_discount','transfer_forfeited','cap_discount','cap_remaining','expected','alt_expected','basis_diff','day_paid'],['event_id','card','ticket_type','expected','reported','difference','fare_subsidy','discount_subsidy','subsidy','status'],['event_id','card','expected','reported','status']]
        columns=choices[index]
        labels={'event_id':'事件','card':'卡号','route':'线路','event_time':'刷卡时间','result':'刷卡状态','reported':'实扣 / 元','ticket_type':'票种','line_group':'线路组','fare_version':'票价版','base_fare':'普通票价','payable_fare':'票种实付','at':'事件时间 UTC','journey':'行程编号','business_day':'业务日','transfer_anchor':'锚点','transfer_entitlement':'换乘权益(普通基数)','transfer_discount':'换乘减免','transfer_forfeited':'放弃权益','cap_remaining':'封顶余量(普通基数)','cap_discount':'封顶减免','expected':'应收 / 元','alt_expected':'影子应收(实付基数)','basis_diff':'口径差异','day_paid':'卡日唯一应收','difference':'差额 / 元','fare_subsidy':'票种让利','discount_subsidy':'优惠补贴','subsidy':'清分补贴','status':'结论','accepted':'采纳行','versions':'版本','tickets':'票种类别','expected_total':'应扣总额','alt_expected_total':'影子应扣总额','daily_caps':'卡日数量','transfer_hits':'换乘次数','subsidy_capped_rows':'补贴封顶行','input':'输入行','quarantine':'隔离行','duplicate':'重复行','blank':'空白行','repeated_headers':'重复表头','encoding':'编码','routes':'线路数','cards':'卡数','journeys':'行程数','records':'记录数','source_lines':'来源行数','sha256':'摘要','ready':'可归档','differences':'差异项'}
        for key,label in {'accepted_inputs': '采纳来源行', 'quarantine_inputs': '隔离来源行', 'output_records': '结果记录', 'input': '输入行', 'excluded': '排除行', 'balanced': '行数平衡', 'expected_total': '预期合计', 'alt_expected_total': '影子预期合计', 'reported_total': '申报合计', 'differences': '差异项', 'blank': '空行', 'repeated_headers': '分段表头', 'encoding': '编码', 'duplicate': '重复行', 'quarantine': '隔离行', 'accepted': '采纳行', 'sha256': '校验摘要', 'ready': '可归档', 'subsidy_total': '清分补贴合计', 'fare_subsidy_total': '票种让利合计', 'discount_subsidy_total': '优惠补贴合计', 'subsidy_capped_rows': '补贴封顶行', 'tickets': '票种类别'}.items(): labels.setdefault(key,label)
        return render_template(f"m{index+1}.html",title=TITLE,short=SHORT,modules=MODULES,index=index,run=run,stage=stage,rows=rows,columns=columns[:12],history=store.history(),labels=labels)
    app.add_url_rule("/",view_func=lambda:page(4))
    for index,(slug,name) in enumerate(MODULES):
        app.add_url_rule("/"+slug,endpoint="page_"+slug,view_func=lambda index=index:page(index))
