import os
from playwright.sync_api import sync_playwright
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); S=R+"/tests"; D=R+"/samples"; APP="file://"+R+"/index.html"
fails=[]

def check(name,cond,info=""):
    print(("PASS " if cond else "FAIL ")+name+("" if cond else f"  -> {info}"))
    if not cond: fails.append(name)

with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome"); pg=b.new_page(accept_downloads=True,viewport={"width":1280,"height":900})
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda m: m.type=="error" and errs.append(m.text))
    dialogs=[]; pg.on("dialog",lambda d:(dialogs.append(d.message), d.accept()))
    pg.goto(APP); pg.wait_for_timeout(800)
    check("accept attr includes xlsx", ".xlsx" in pg.get_attribute("#file","accept"))
    check("timer idle before grading", pg.inner_text("#timerText")=="00:00")
    pg.set_input_files("#file",D+"/sample.xlsx"); pg.wait_for_timeout(600)
    opts=pg.eval_on_selector_all("#course option","o=>o.map(x=>x.value)")
    check("unique courses", opts==["","Course A","Course B"], opts)
    pg.set_input_files("#file",D+"/second.xlsx"); pg.wait_for_timeout(600)
    opts=pg.eval_on_selector_all("#course option","o=>o.map(x=>x.value)")
    check("second upload replaces courses", opts==["","Course A","Course C"], opts)
    pg.set_input_files("#file",D+"/sample.xlsx"); pg.wait_for_timeout(600)
    pg.select_option("#course","Course A"); pg.wait_for_timeout(1300)
    check("timer ticking after course select", pg.inner_text("#timerText")!="00:00", pg.inner_text("#timerText"))
    check("export disabled without name", pg.is_disabled("#download") and "instructor" in pg.inner_text("#whyDisabled"))
    pg.fill("#instructor","Dr, \"Test\""); pg.wait_for_timeout(100)
    check("export enabled with name", not pg.is_enabled("#download")==False)
    st=pg.inner_text("#stats").replace("\n"," ").title().replace("Std Dev","Std dev"); print("  stats:",st)
    # compute expected from file
    
    import openpyxl
    ws=openpyxl.load_workbook(D+"/sample.xlsx").active
    marks=[r[2] for r in ws.iter_rows(min_row=2,values_only=True) if r[1]=="Course A"]
    
    import statistics
    check("min/max correct", f"Min {min(marks)}" in st and f"Max {max(marks)}" in st, st)
    check("mean correct", f"Mean {statistics.mean(marks):.2f}" in st, (statistics.mean(marks),st))
    check("median correct", f"Median {statistics.median(marks):g}" in st, statistics.median(marks))
    
    def exp_grade(m,mins):
        for g,v in mins:
            if m>=v: return g
    D0=[("A",80),("A-",70),("B",60),("B-",50),("C",40),("C-",30),("D",20),("E",0)]
    dist=pg.eval_on_selector_all("#distBody tr","t=>t.map(r=>[r.children[0].innerText,r.children[2].innerText])")
    exp={g:0 for g,_ in D0}
    for m in marks: exp[exp_grade(m,D0)]+=1
    check("distribution matches", dict((g,int(c)) for g,c in dist)==exp, (dist,exp))
    check("100 and 0 counted (total)", sum(int(c) for _,c in dist)==len(marks))
    
    # edit cutoff: A min 85 -> A- max 84
    pg.fill("#min-A","85"); pg.wait_for_timeout(150)
    check("max cascades", pg.inner_text("#max-A-")=="84")
    
    # invalid: A- min 90 > A
    pg.fill("#min-A-","90"); pg.wait_for_timeout(150)
    check("invalid blocks export", pg.is_disabled("#download") and not pg.is_hidden("#rangeError"))
    check("invalid card highlighted", "invalid" in pg.get_attribute("#card-A-","class"))
    pg.fill("#min-A-","70"); pg.wait_for_timeout(150)
    
    # single-value band allowed
    pg.fill("#min-A","100"); pg.wait_for_timeout(150)
    check("A=100..100 allowed", pg.is_enabled("#download"))
    pg.fill("#min-A",""); pg.wait_for_timeout(150)
    check("blank cutoff invalid", pg.is_disabled("#download"))
    pg.fill("#min-A","80"); pg.wait_for_timeout(150)
    
    # stepper
    pg.click("#card-B button[data-step='1']"); pg.wait_for_timeout(100)
    check("stepper +1", pg.input_value("#min-B")=="61" and pg.inner_text("#max-B-")=="60")
    
    # borderline
    bl=pg.inner_text("#blList"); print("  borderline:",bl[:160].replace("\n"," | "))
    btn=pg.query_selector("#blList button")
    if btn:
        label=btn.inner_text(); btn.click(); pg.wait_for_timeout(150)
        g,v=label.replace("Lower ","").split(" to ")
        check("borderline button lowers cutoff", pg.input_value("#min-"+g)==v, label)
    
    # reset single confirm
    dialogs.clear(); pg.click("#resetRanges"); pg.wait_for_timeout(150)
    check("reset single confirm", len(dialogs)==1, dialogs)
    check("reset restored", pg.input_value("#min-B")=="60")
    
    # table
    pg.fill("#search","A90"); pg.wait_for_timeout(100)
    check("search filters", pg.eval_on_selector_all("#studentBody tr","t=>t.length")==4)
    pg.fill("#search",""); pg.select_option("#gradeFilter","A"); pg.wait_for_timeout(100)
    check("grade filter", pg.eval_on_selector_all("#studentBody tr","t=>t.length")==exp["A"])
    pg.select_option("#gradeFilter","")
    
    # export
    pg.click("#download"); pg.wait_for_timeout(200)
    check("review dialog open", pg.is_visible("#exportDlg"))
    with pg.expect_download() as dl: pg.click("#dlgConfirm")
    d=dl.value; txt=open(d.path(),encoding="utf-8-sig",newline="").read()
    check("filename", d.suggested_filename.startswith("grades_Course_A_"), d.suggested_filename)
    lines=txt.strip().split("\r\n")
    check("csv instructor escaped", lines[0]=='Instructor,"Dr, ""Test"""', lines[0])
    check("csv course no leading space", lines[1]=="Course,Course A", lines[1])
    rows=lines[lines.index("BITS ID,Total Marks,Grade")+1:]
    check("csv has all students", len(rows)==len(marks), (len(rows),len(marks)))
    ok=all(r.split(",")[2]==exp_grade(int(r.split(",")[1]),D0) for r in rows)
    check("csv grades correct", ok)
    check("thank-you shown", "completed grading" in pg.inner_text("#thankyou"))
    t1=pg.inner_text("#timerText"); pg.wait_for_timeout(1200)
    check("timer stops on export", pg.inner_text("#timerText")==t1)
    
    # empty course -> placeholder
    pg.select_option("#course",""); pg.wait_for_timeout(100)
    check("placeholder hides workspace", pg.is_hidden("#gradingArea"))
    
    # text marks
    pg.set_input_files("#file",D+"/text.xlsx"); pg.wait_for_timeout(600)
    check("single course auto-selected", pg.input_value("#course")=="Course T")
    check("text marks mean", "MEAN 72.33" in pg.inner_text("#stats").replace("\n"," "), pg.inner_text("#stats"))
    pg.set_input_files("#file",D+"/same.xlsx"); pg.wait_for_timeout(600)
    check("identical marks ok", "STD DEV 0" in pg.inner_text("#stats").replace("\n"," "))
    pg.set_input_files("#file",D+"/messy.xlsx"); pg.wait_for_timeout(600)
    rep=pg.inner_text("#fileReport"); print("  messy report:",rep.replace("\n"," | ")[:600])
    opts=pg.eval_on_selector_all("#course option","o=>o.map(x=>x.value)")
    check("messy: trimmed course merged", opts==["","Course M"], opts)
    check("messy: 3 valid (82, 79.5->80, 71)", "3 students loaded" in rep)
    for s in ["duplicate","outside 0–100","blank marks","not a number","Missing BITS ID","rounded to 80"]:
        check("messy reports "+s, s in rep)
    pg.set_input_files("#file",D+"/wrongcols.xlsx"); pg.wait_for_timeout(600)
    check("wrong columns error", "Missing column: BITS ID" in pg.inner_text("#fileReport"), pg.inner_text("#fileReport"))
    pg.set_input_files("#file",[]); pg.wait_for_timeout(200)
    check("no JS errors", not errs, errs)

    pg.set_input_files("#file",D+"/sample.xlsx"); pg.wait_for_timeout(600); pg.select_option("#course","Course A"); pg.wait_for_timeout(300)
    pg.screenshot(path=S+"/screenshot_desk.png",full_page=True)
    pg.emulate_media(color_scheme="dark"); pg.screenshot(path=S+"/screenshot_dark.png",full_page=True); pg.emulate_media(color_scheme="light")
    pg.set_viewport_size({"width":390,"height":844}); pg.wait_for_timeout(200)
    sw=pg.evaluate("document.documentElement.scrollWidth")
    check("no horizontal scroll on mobile", sw<=390, sw)
    pg.screenshot(path=S+"/screenshot_mobile.png",full_page=True)
    b.close()

print("FAILURES:",fails)
