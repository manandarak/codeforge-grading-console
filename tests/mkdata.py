import openpyxl, random, os
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","samples")
def wb(name, rows, header=("BITS ID","Course","Total Marks")):
    w=openpyxl.Workbook(); s=w.active; s.append(header)
    for r in rows: s.append(r)
    w.save(os.path.join(D,name))
random.seed(1)
rows=[]
for c,n,mu in [("Course A",40,62),("Course B",25,55)]:
    for i in range(n):
        rows.append((f"2024{c[-1]}{i:03d}",c,max(0,min(100,round(random.gauss(mu,15))))))
rows += [("2024A900","Course A",100),("2024A901","Course A",0),("2024A902","Course A",80),("2024A903","Course A",79)]
wb("sample.xlsx",rows)
wb("second.xlsx",[("2024C001","Course C",70),("2024C002","Course C",45),("2024A001","Course A",90)])
# messy: text marks, decimal, out-of-range, blank, duplicate id, header w/ spaces
wb("messy.xlsx",[("2024M001","Course M","82"),("2024M002","Course M",79.5),("2024M003","Course M",105),
  ("2024M004","Course M",None),("2024M001","Course M",60),("2024M005","Course M",-3),("2024M006"," Course M ",71),("","Course M",50),("2024M007","Course M","abc")],
  header=(" BITS ID ","Course","Total Marks "))
wb("same.xlsx",[(f"2024S{i:03d}","Course S",75) for i in range(5)])
wb("text.xlsx",[("2024T001","Course T","82"),("2024T002","Course T","71"),("2024T003","Course T","64")])
wb("wrongcols.xlsx",[("x","y",1)],header=("Name","Subject","Score"))
print(os.listdir(D))
