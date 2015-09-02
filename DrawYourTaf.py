import sys, os, string, time, copy, math
import Tkinter as tk
import tkMessageBox
import re

pmwpath = "/data/local/"
sys.path.append(pmwpath)
import Pmw

####### Configure #######

tafout = './tafout/'
tafdir2 = './tafout2/'
sites = ["KCRW", "KHTS", "KPKB", "KCKB", "KEKN", "KBKW"]

width = 800
height = 300
height_vis = 220

axis_color = "black"
fx_color = "black"
dot_color = "#D1FFBD"

pct_width_raxis = 0.95
pct_width_laxis = 0.05
pct_top = 0.1
pct_bot = 0.9

pct_graph_width = pct_width_raxis - pct_width_laxis
pct_graph_height = pct_bot - pct_top
graph_height = pct_graph_height * height
graph_height_vis = pct_graph_height * height_vis
#########################
# heights = ["080","031","020","010","006","002","001"]
heights = ["100", "030", "020", "010", "005", "001"]
visbys = ["10", "6", "3", "1", "0.5", "0.25", "0.1"]
points = []

tag1 = "theline"

_ValidVsby = { \
    '0': 0.1,
    'M1/4': 0.1,
    '1/4': 0.25,
    '1/2': 0.5,
    '3/4': 0.75,
    '1': 1.0,
    '1 1/2': 1.5,
    '2': 2.0,
    '3': 3.0,
    '4': 4.0,
    '5': 5.0,
    '6': 6.0,
    'P6': 10.0
    }

(year, month, day, jhour, jmin, jsec, wday, yday, dst) = time.gmtime()


class Ddict(dict):
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)


class CanvasDnD(tk.Frame):
    def __init__(self, master):
        self.master = master
        self.loc = self.dragged = 0

        self.tafbegin_group, self.tafend_group, self.begin_month, self.begin_day, self.begin_year, self.end_month, self.end_day, self.end_year = '', '', '', '', '', '', '', ''
        self.rad = {}
        self.saved = {}
        self.test = 0
        self.cloud_level = tk.StringVar()

        tk.Frame.__init__(self, master)

        labelcig = tk.Label(self, text="Ceiling")
        labelcig.pack(pady=10)

        canvas = tk.Canvas(self, width=800, height=300, relief=tk.RIDGE, background="white", borderwidth=1)
        self.c = canvas

        # Cig Canvas #############
        # top and bottom
        self.c.create_line(pct_width_laxis * width, pct_top * height, pct_width_raxis * width, pct_top * height,
                           fill=axis_color)
        self.c.create_line(pct_width_laxis * width, pct_bot * height, pct_width_raxis * width, pct_bot * height,
                           fill=axis_color)

        # left and right
        self.c.create_line(pct_width_laxis * width, pct_top * height, pct_width_laxis * width, pct_bot * height,
                           fill=axis_color)
        self.c.create_line(pct_width_raxis * width, pct_top * height, pct_width_raxis * width, pct_bot * height,
                           fill=axis_color)

        x, y1 = self.toGraphCoordfromTAF(0, 10000)
        x, y2 = self.toGraphCoordfromTAF(0, 3000)
        x, y3 = self.toGraphCoordfromTAF(0, 1000)
        x, y4 = self.toGraphCoordfromTAF(0, 500)
        x, y5 = self.toGraphCoordfromTAF(0, 100)

        # VFR
        self.c.create_rectangle(pct_width_laxis * width, pct_top * height, pct_width_raxis * width, y2, fill="#A9FFA6")

        # MVFR
        self.c.create_rectangle(
            pct_width_laxis * width,
            y2,
            pct_width_raxis * width,
            y3,
            fill="#FFFF58")

        # IFR
        self.c.create_rectangle(
            pct_width_laxis * width,
            y3,
            pct_width_raxis * width,
            y4,
            fill="#FFCC9D")

        # LIFR
        self.c.create_rectangle(
            pct_width_laxis * width,
            y4,
            pct_width_raxis * width,
            y5,
            fill="#FFD1F3")

        (year, month, tafday, tafhour, tmin, jsec, wday, yday, dst) = time.gmtime()
        if tafhour > 18 and tafhour <= 23:
            self.tafphour = 18
        elif tafhour > 12 and tafhour <= 18:
            self.tafphour = 12
        elif tafhour > 6 and tafhour <= 12:
            self.tafphour = 6
        elif tafhour > 0 and tafhour <= 6:
            self.tafphour = 0

        self.tafpackage = (year, month, tafday, self.tafphour, tmin, jsec, wday, yday, dst)
        print tafhour
        # sys.exit()

        for i in range(25):
            (year, month, tafday, tafhour, tmin, jsec, wday, yday, dst) = time.gmtime(
                time.mktime(self.tafpackage) + i * 3600)
            # tafhour = self.tafphour + i
            # time and vertical lines/X-axis Legend
            self.c.create_text(i * pct_graph_width * width / 24 + pct_width_laxis * width, height * 0.05, text=tafhour,
                               fill=axis_color)
            self.c.create_line(i * pct_graph_width * width / 24 + pct_width_laxis * width, pct_top * height,
                               i * pct_graph_width * width / 24 + pct_width_laxis * width, pct_bot * height,
                               fill=axis_color, dash=(4, 4))

        for index, i in enumerate(range(len(heights))):
            j = float(heights[i]) * 100
            self.c.create_text(pct_width_laxis * width - 20,
                               abs(graph_height - (graph_height * (math.log10(j) - 2) / 2)) + pct_top * height,
                               text=heights[index], fill=axis_color)


        # other important thresholds
        x, y = self.toGraphCoordfromTAF(0, 2000)
        self.c.create_line(pct_width_laxis * width, y,
                           24 * pct_graph_width * width / 24 + pct_width_laxis * width, y, fill=axis_color, dash=(4, 4))

        x, y = self.toGraphCoordfromTAF(0, 600)
        self.c.create_line(pct_width_laxis * width, y,
                           24 * pct_graph_width * width / 24 + pct_width_laxis * width, y, fill=axis_color, dash=(4, 4))

        canvas.pack(expand=1, fill=tk.BOTH)
        canvas.tag_bind("Ceiling", "<ButtonPress-2>", self.down)
        canvas.tag_bind("Ceiling", "<ButtonRelease-2>", self.chkup)
        canvas.tag_bind("Ceiling", "<Enter>", self.enter)
        canvas.tag_bind("Ceiling", "<Leave>", self.leave)

        self.c.bind("<Button-1>", self.drawFx)
        self.c.bind("<Button-3>", self.deletePoint)
        # VIS CANVAS ##########################
        labelvis = tk.Label(self, text="Visibility")
        labelvis.pack(pady=10)

        canvas_vis = tk.Canvas(self, width=800, height=height_vis, relief=tk.RIDGE, background="white", borderwidth=1)
        self.cv = canvas_vis


        # top and bottom
        self.cv.create_line(pct_width_laxis * width, pct_top * height_vis, pct_width_raxis * width,
                            pct_top * height_vis, fill=axis_color)
        self.cv.create_line(pct_width_laxis * width, pct_bot * height_vis, pct_width_raxis * width,
                            pct_bot * height_vis, fill=axis_color)

        # left and right
        self.cv.create_line(pct_width_laxis * width, pct_top * height_vis, pct_width_laxis * width,
                            pct_bot * height_vis, fill=axis_color)
        self.cv.create_line(pct_width_raxis * width, pct_top * height_vis, pct_width_raxis * width,
                            pct_bot * height_vis, fill=axis_color)

        x, y1 = self.toGraphCoordfromTAF_vis(0, 10)
        x, y2 = self.toGraphCoordfromTAF_vis(0, 6)
        x, y3 = self.toGraphCoordfromTAF_vis(0, 3)
        x, y4 = self.toGraphCoordfromTAF_vis(0, 1)
        x, y5 = self.toGraphCoordfromTAF_vis(0, 0.1)

        # VFR
        self.cv.create_rectangle(pct_width_laxis * width, pct_top * height_vis, pct_width_raxis * width, y2,
                                 fill="#A9FFA6")

        # MVFR
        self.cv.create_rectangle(
            pct_width_laxis * width,
            y2,
            pct_width_raxis * width,
            y3,
            fill="#FFFF58")

        # IFR
        self.cv.create_rectangle(
            pct_width_laxis * width,
            y3,
            pct_width_raxis * width,
            y4,
            fill="#FFCC9D")

        # LIFR
        self.cv.create_rectangle(
            pct_width_laxis * width,
            y4,
            pct_width_raxis * width,
            y5,
            fill="#FFD1F3")

        x, y = self.toGraphCoordfromTAF_vis(0, 2)
        self.cv.create_line(pct_width_laxis * width, y,
                            24 * pct_graph_width * width / 24 + pct_width_laxis * width, y, fill=axis_color,
                            dash=(4, 4))
        x, y = self.toGraphCoordfromTAF_vis(0, 0.5)
        self.cv.create_line(pct_width_laxis * width, y,
                            24 * pct_graph_width * width / 24 + pct_width_laxis * width, y, fill=axis_color,
                            dash=(4, 4))
        x, y = self.toGraphCoordfromTAF_vis(0, 0.25)
        self.cv.create_line(pct_width_laxis * width, y,
                            24 * pct_graph_width * width / 24 + pct_width_laxis * width, y, fill=axis_color,
                            dash=(4, 4))

        # x-axis set-up
        for i in range(25):
            (year, month, tafday, tafhour, tmin, jsec, wday, yday, dst) = time.gmtime(
                time.mktime(self.tafpackage) + i * 3600)
            # time and vertical lines/X-axis Legend
            self.cv.create_text(i * pct_graph_width * width / 24 + pct_width_laxis * width, height_vis * 0.05,
                                text=tafhour, fill=axis_color)
            self.cv.create_line(i * pct_graph_width * width / 24 + pct_width_laxis * width, pct_top * height_vis,
                                i * pct_graph_width * width / 24 + pct_width_laxis * width, pct_bot * height_vis,
                                fill=axis_color, dash=(4, 4))

        # y-axis set-up
        for index, i in enumerate(range(len(visbys))):
            j = float(visbys[i])
            test = abs(graph_height_vis - (
            (graph_height_vis * math.log10(j) / 2) + graph_height_vis / 2.0)) + pct_top * height_vis
            self.cv.create_text(pct_width_laxis * width - 20, test, text=visbys[index], fill=axis_color)

        self.cv.pack(expand=1, fill=tk.BOTH)
        self.cv.tag_bind("Visibility", "<ButtonPress-2>", self.down_vis)
        self.cv.tag_bind("Visibility", "<ButtonRelease-2>", self.chkup)
        self.cv.tag_bind("Visibility", "<Enter>", self.enter)
        self.cv.tag_bind("Visibility", "<Leave>", self.leave)
        self.cv.bind("<Button-1>", self.drawFx_vis)
        self.cv.bind("<Button-3>", self.deletePoint_vis)


        # Controls ##########################
        self.Frame_right = tk.Frame(root, bd=2, relief='flat', padx=5, pady=5, width=width)
        self.Frame_right.grid(row=0, column=1)

        self.Frame = tk.Frame(self.Frame_right, bd=2, relief='groove', padx=5, pady=5, width=width)
        self.Frame.grid(row=1, column=0, pady=40)

        self.taflabel = tk.Label(self.Frame_right,
                                 text="Click on graphs \nto generate TAF\n\nTAF will show up here after\n you have both visibility and ceilings.\n\n1) Left click will place points\n2) Middle click to drag/move\n3) Right click to delete",
                                 bd=3, bg='white', relief="raised", anchor=tk.W, justify=tk.LEFT)
        self.taflabel.grid(row=0, column=0, sticky=tk.W, padx=10)


        # self.cloud_level.set('Low')
        # layers = ["Ceiling"]#"High","Mid","Low",]
        # for i in range(len(layers)):
        # self.rad[i] = tk.Radiobutton(self.Frame,text=layers[i],variable=self.cloud_level,value=layers[i], selectcolor="yellow",fg='#005306')
        # self.rad[i].grid(row=i,column=5)

        ########################
        cigarr = ["FEW", "SCT", "BKN", "OVC"]
        # self.skypick = tk.StringVar()
        # self.skyoption = Pmw.OptionMenu(self.Frame,
        # menubutton_textvariable = self.skypick,
        # items = cigarr,
        # initialitem="OVC",
        # command = lambda i=0: self.drawLine()
        # )
        # self.skyoption.grid(row=0,column=6)

        # self.skypick = tk.StringVar()
        # self.skyoption = Pmw.OptionMenu(self.Frame,
        # menubutton_textvariable = self.skypick,
        # items = cigarr,
        # initialitem="BKN",
        # command = lambda i=0: self.drawLine()
        # )
        # self.skyoption.grid(row=1,column=6)

        self.skypick = tk.StringVar()
        self.skyoption = Pmw.OptionMenu(self.Frame,
                                        menubutton_textvariable=self.skypick,
                                        items=cigarr,
                                        initialitem="BKN",
                                        command=lambda i=0: self.drawLine()
                                        )
        self.skyoption.grid(row=1, column=1)
        ####################
        self.sitelabel = tk.Label(self.Frame, text="Site:", bd=3, fg='#005306', relief="flat", anchor=tk.W,
                                  justify=tk.LEFT)
        self.sitelabel.grid(row=0, column=0, sticky=tk.W, padx=10)

        self.ciglabel = tk.Label(self.Frame, text="Ceiling:", bd=3, fg='#005306', relief="flat", anchor=tk.W,
                                 justify=tk.LEFT)
        self.ciglabel.grid(row=1, column=0, sticky=tk.W, padx=10)

        self.wxlabel = tk.Label(self.Frame, text="Wx:", bd=3, fg='#005306', relief="flat", anchor=tk.W, justify=tk.LEFT)
        self.wxlabel.grid(row=3, column=0, sticky=tk.W, padx=10)

        self.wxpick = tk.StringVar()
        wxarr = ['', "FG", "BR", "FZFG", "-RA", "RA", "+RA", "-SN", "SN", "+SN", "-DZ", "DZ", "+DZ", "-TSRA", "TSRA",
                 "+TSRA"]
        self.wxoption = Pmw.OptionMenu(self.Frame,
                                       menubutton_textvariable=self.wxpick,
                                       items=wxarr,
                                       initialitem="",
                                       command=lambda i=0: self.labelTaf()

                                       )
        self.wxoption.grid(row=3, column=1)

        self.wxpick2 = tk.StringVar()
        self.wx2option = Pmw.OptionMenu(self.Frame,
                                        menubutton_textvariable=self.wxpick2,
                                        items=wxarr,
                                        initialitem="",
                                        command=lambda i=0: self.labelTaf()
                                        )
        self.wx2option.grid(row=3, column=2)

        self.sitepick = tk.StringVar()
        self.siteoption = Pmw.OptionMenu(self.Frame,
                                         menubutton_textvariable=self.sitepick,
                                         items=sites,
                                         initialitem="KCRW",
                                         command=lambda i=0: self.readTAF()
                                         )
        self.siteoption.grid(row=0, column=1)

        self.saveTAF = tk.Button(self.Frame, text="Save", command=self.saveTAF, bg="#DCFF92")
        self.saveTAF.grid(row=4, column=1, pady=20)

        self.saveTAF = tk.Button(self.Frame, text="Combine TAFs", command=self.combineTAF, bg="#DCFF92")
        self.saveTAF.grid(row=5, column=1, pady=0)

        statuslabel = tk.Label(self.Frame_right, text="Status:", bd=0, relief="flat", anchor=tk.W, justify=tk.LEFT)
        statuslabel.grid(row=2, column=0, sticky=tk.W)

        self.sitelabels = {}
        for index, site in enumerate(sites):
            self.sitelabels[site] = tk.Label(self.Frame_right, text=" " + site + " ", bd=2, fg='black', bg='#B2B4A8',
                                             relief="raised", anchor=tk.W, justify=tk.LEFT)
            self.sitelabels[site].grid(row=index + 3, column=0, sticky=tk.W)

        self.cleanTAFDirectory()
        self.readTAF()

    def cleanTAFDirectory(self):
        for i in sites:
            try:
                os.remove(tafout + 'TAF.' + i)
            except:
                print "Could not remove " + tafout + 'TAF.' + i

    def saveTAF(self):
        taf = self.labelTaf() + '=\n\n'
        print taf
        _id = self.sitepick.get()
        self.saved[_id] = 1
        self.sitelabels[_id].configure(bg='light green', fg='black')
        f = open(tafout + 'TAF.' + _id, 'w')
        f.write(taf)
        f.close()
        print self.saved

    def combineTAF(self):
        f = open(tafout + 'TAF', 'w')
        f.write('FTUS46 KPQR 202300\n')
        ok = 0
        for i in sites:
            try:
                f2 = open(tafout + 'TAF.' + i, 'r')
                for i2 in f2.readlines():
                    f.write(i2)
                f2.close()
            except:
                self.sitelabels[i].configure(bg='red', fg='white')
                ok = 1
        if ok == 1:
            tkMessageBox.showinfo("Ok", "There are some sites you haven't saved yet.")

        f.close()

    def drawFx(self, event):
        if event.x > pct_width_laxis * width and event.x < pct_width_raxis * width and event.y > pct_top * height - 20 and event.y < pct_bot * height:
            self.c.create_oval(event.x - 4, event.y - 4, event.x + 4, event.y + 4, fill=dot_color, tag="Ceiling")
            self.drawLine()
            return points

    def drawFx_vis(self, event):
        if event.x > pct_width_laxis * width and event.x < pct_width_raxis * width and event.y > pct_top * height_vis and event.y < pct_bot * height_vis:
            self.cv.create_oval(event.x - 4, event.y - 4, event.x + 4, event.y + 4, fill=dot_color, tag="Visibility")
            self.drawVisLine()
            return points

    def lt10(self, x):
        if x < 10:
            return "0" + str(x)
        else:
            return str(x)

    def formatTime(self, graphtime):
        # (year,month,tafday,tafhour,tmin,jsec,wday,yday,dst) = time.gmtime(time.mktime(time.gmtime())+int(graphtime)*3600)
        (year, month, tafday, tafhour, tmin, jsec, wday, yday, dst) = time.gmtime(
            time.mktime(self.tafpackage) + int(graphtime) * 3600)
        if tafhour < 10:
            tafhour = "0" + str(int(tafhour))
        else:
            tafhour = str(int(tafhour))
        if tafday < 10:
            tafday = "0" + str(int(tafday))
        else:
            tafday = str(int(tafday))
        return tafday + tafhour

    def formatCig(self, graphCig):
        graphCig = int(graphCig / 100)
        if graphCig < 10:
            graphCig = '00' + str(int(round(graphCig)))
        elif graphCig < 100:
            if graphCig > 50:
                graphCig = '0' + str(int(round(graphCig, -1)))
            else:
                graphCig = '0' + str(int(graphCig))
        elif graphCig >= 100 and graphCig < 110:
            graphCig = '150'
        elif graphCig >= 110 and graphCig < 115:
            graphCig = '200'
        elif graphCig >= 115 and graphCig < 119:
            graphCig = '250'
        elif graphCig >= 119:
            graphCig = 'SKC'
        else:
            graphCig = str(int(graphCig))
        if graphCig == '000':
            graphCig = '001'
        return graphCig

    def formatVis(self, graphVis):
        wxtype = self.wxpick.get()
        if wxtype != '':
            wxtype2 = ' ' + self.wxpick2.get()
        else:
            wxtype2 = '' + self.wxpick2.get()

        if graphVis <= 0.5 and wxtype == "BR":
            wxtype = " FG"
        if graphVis > 0.5 and wxtype == "FG":
            wxtype = " BR"
        if graphVis < 0.1:
            graphVis = ' 0SM' + wxtype + wxtype2
        elif graphVis < 0.25:
            graphVis = ' M1/4SM' + wxtype + wxtype2
        elif graphVis >= 0.25 and graphVis < 0.5:
            graphVis = ' 1/4SM' + wxtype + wxtype2
        elif graphVis >= 0.5 and graphVis < 0.75:
            graphVis = ' 1/2SM ' + wxtype + wxtype2
        elif graphVis >= 0.75 and graphVis < 1.0:
            graphVis = ' 3/4SM' + wxtype + wxtype2
        elif graphVis >= 1.0 and graphVis < 1.5:
            graphVis = ' 1SM' + wxtype + wxtype2
        elif graphVis >= 1.5 and graphVis < 2.0:
            graphVis = ' 1 1/2SM' + wxtype + wxtype2
        elif graphVis > 6.9:
            graphVis = 'P6SM'
        else:
            graphVis = str(int(graphVis)) + 'SM ' + wxtype + wxtype2
        return graphVis

    def labelTaf(self):

        taf = ''
        vis1 = ''

        points = self.c.find_withtag("Ceiling")
        vpoints = self.cv.find_withtag("Visibility")
        cigs = []
        vis = []
        for index, i in enumerate(points):
            xy = self.c.coords(i)
            x, y = self.fromGraphCoordtoTAF(xy[0] + 3, xy[1] + 3)

            taftime = self.formatTime(x)
            cigs.append([str(taftime), 'c', y])
            if index == 0:
                cig1 = y

        for index, i in enumerate(vpoints):
            xy = self.cv.coords(i)
            x, y = self.fromGraphCoordtoTAF_vis(xy[0] + 3, xy[1] + 3)
            taftime = self.formatTime(x)
            vis.append([str(taftime), 'v', y])
            if index == 0:
                vis1 = y

        merged = cigs + vis
        merged.sort()
        tafdata = {}
        for index, i in enumerate(merged):
            if i[1] == 'c':
                cig = i[2]
            else:
                vis = i[2]

            if index == 0:
                # print i[0]
                tafdata[i[0]] = Ddict(dict)
                tafdata[i[0]]['vis'] = vis1
                tafdata[i[0]]['cig'] = cig1

                timecheck = i[0]
            else:
                if i[0] != timecheck:
                    # print i[0]
                    tafdata[i[0]] = Ddict(dict)
                    tafdata[i[0]]['vis'] = vis
                    tafdata[i[0]]['cig'] = cig
                    timecheck = i[0]
                else:
                    tafdata[i[0]] = Ddict(dict)
                    tafdata[i[0]]['vis'] = vis
                    tafdata[i[0]]['cig'] = cig
                    # print 'duplicate'
                    timecheck = i[0]

        early, late = [], []
        for i in tafdata.keys():
            if int(i[0:2]) < 10:
                early.append(i)
            else:
                late.append(i)
        if len(late) >= 1:
            mytaf = sorted(late) + sorted(early)
        else:
            mytaf = sorted(tafdata.keys())

        mywind = '00000'

        ##for index,i in enumerate(vpoints):
        for index, i in enumerate(mytaf):
            if index == 0:
                taf = "TAF\n" + self.sitepick.get() + ' ' + self.lt10(day) + self.lt10(jhour) + self.lt10(
                    jmin) + "Z " + self.lt10(day) + self.lt10(self.tafphour) + "/04" + self.lt10(
                    self.tafphour) + " 00000KT "
                myvis = self.formatVis(tafdata[mytaf[0]]['vis'])
                mycig = self.formatCig(tafdata[mytaf[0]]['cig'])
                if mycig != 'SKC':
                    taf = taf + ' ' + myvis + ' ' + self.skypick.get() + mycig + "\n"
                else:
                    taf = taf + ' ' + myvis + ' ' + mycig + "\n"
            else:

                myvis = self.formatVis(tafdata[mytaf[index]]['vis'])
                mycig = self.formatCig(tafdata[mytaf[index]]['cig'])
                if mycig != 'SKC':
                    taf = taf + '   FM' + mytaf[
                        index] + '00 ' + mywind + 'KT ' + myvis + ' ' + self.skypick.get() + mycig + "\n"
                else:
                    taf = taf + '   FM' + mytaf[index] + '00 ' + mywind + 'KT ' + myvis + ' ' + mycig + "\n"

        self.taflabel.configure(text=taf + '=')
        return taf

    def deletePoints(self):
        cigs = self.c.find_withtag("Ceiling")
        for i in cigs:
            self.c.delete(i)

        vis = self.cv.find_withtag("Visibility")
        for i in vis:
            self.cv.delete(i)

    def deletePoint(self, event):
        point = self.c.find_closest(event.x, event.y)
        cigs = self.c.find_withtag("Ceiling")
        foundpoint = 0
        tempindex = []
        for i in cigs:
            tempindex.append(self.c.coords(i)[0])
            if i == point[0]:
                self.c.delete(i)
                self.drawLine()

    def deletePoint_vis(self, event):
        point = self.cv.find_closest(event.x, event.y)
        vis = self.cv.find_withtag("Visibility")
        for i in vis:
            if i == point[0]:
                self.cv.delete(i)
                self.drawVisLine()

    def drawLine(self):
        # try:
        line = self.c.find_withtag("line")
        self.c.delete(line)
        points = self.c.find_withtag("Ceiling")
        plot = []
        for i in points:
            coords = self.c.coords(i)
            if len(plot) > 1:
                plot.append(coords[0] + 3)
                plot.append(plot[len(plot) - 2])
            plot.append(coords[0] + 3)
            plot.append(coords[1] + 5)

        try:
            self.test = self.c.create_line(plot, tags="line", fill=fx_color, width=2.0)
        except:
            pass
        self.labelTaf()
        self.c.tag_raise("Ceiling")

    def drawVisLine(self):
        line = self.cv.find_withtag("line_vis")
        self.cv.delete(line)
        points = self.cv.find_withtag("Visibility")
        plot = []
        for i in points:
            coords = self.cv.coords(i)
            if len(plot) > 1:
                plot.append(coords[0] + 3)
                plot.append(plot[len(plot) - 2])
            plot.append(coords[0] + 3)
            plot.append(coords[1] + 5)

        try:
            self.test = self.cv.create_line(plot, tags="line_vis", fill=fx_color, width=2.0)
        except:
            pass
        self.labelTaf()
        self.cv.tag_raise("Visibility")

    def toGraphCoordfromTAF_vis(self, x, y):
        return x * pct_graph_width * width / 24 + pct_width_laxis * width, abs(
            graph_height_vis - ((graph_height_vis * math.log10(y) / 2) + graph_height_vis / 2.0)) + pct_top * height_vis

    def fromGraphCoordtoTAF_vis(self, x, y):
        gh = graph_height_vis
        # funny stuff with converting from log to linear scale set indices from 0 to 2 then transform and then set them back
        exponent = abs(2 - (((((y - pct_top * height_vis + gh) * 2) / gh) - 3) + 1)) - 1
        return ((x - pct_width_laxis * width) * 24) / (pct_graph_width * width), math.pow(10, exponent)

    def toGraphCoordfromTAF(self, x, y):
        return x * pct_graph_width * width / 24 + pct_width_laxis * width, abs(
            graph_height - (graph_height * (math.log10(y) - 2) / 2)) + pct_top * height

    def fromGraphCoordtoTAF(self, x, y):
        gh = graph_height
        exponent = 2 - ((((y - pct_top * height + gh) * 2) / gh) - 2)
        return ((x - pct_width_laxis * width) * 24) / (pct_graph_width * width), math.pow(10, exponent) * 100

    def down(self, event):
        self.loc = 1
        self.dragged = 0
        event.widget.bind("<Motion>", self.motion)

    def down_vis(self, event):
        self.loc = 1
        self.dragged = 0
        event.widget.bind("<Motion>", self.motion_vis)

    def motion(self, event):
        if event.x > pct_width_laxis * width and event.x < pct_width_raxis * width and event.y > pct_top * height - 20 and event.y < pct_bot * height:
            root.config(cursor="dotbox")
            cnv = event.widget
            xy = cnv.canvasx(event.x) - 1.3, cnv.canvasy(event.y) - 1.3
            points = event.widget.coords(tk.CURRENT)
            anchors = copy.copy(points[:2])

            for idx in range(len(points)):
                mouse = xy[idx % 2]
                zone = anchors[idx % 2]
                points[idx] = points[idx] - zone + mouse

            apply(event.widget.coords, [tk.CURRENT] + points)
            self.drawLine()

    def motion_vis(self, event):
        if event.x > pct_width_laxis * width and event.x < pct_width_raxis * width and event.y > pct_top * height_vis and event.y < pct_bot * height_vis:
            root.config(cursor="dotbox")
            cnv = event.widget
            xy = cnv.canvasx(event.x) - 1.3, cnv.canvasy(event.y) - 1.3
            points = event.widget.coords(tk.CURRENT)
            anchors = copy.copy(points[:2])

            for idx in range(len(points)):
                mouse = xy[idx % 2]
                zone = anchors[idx % 2]
                points[idx] = points[idx] - zone + mouse

            apply(event.widget.coords, [tk.CURRENT] + points)
            self.drawVisLine()

    def leave(self, event):
        self.loc = 0

    def enter(self, event):
        self.loc = 1
        if self.dragged == event.time:
            self.up(event)

    def chkup(self, event):
        event.widget.unbind("<Motion>")
        root.config(cursor="crosshair")
        self.target = event.widget.find_withtag(tk.CURRENT)

        if self.loc:  # is button released in same widget as pressed?
            self.up(event)
        else:
            self.dragged = event.time

    def up(self, event):
        event.widget.unbind("<Motion>")
        if (self.target == event.widget.find_withtag(tk.CURRENT)):
            pass
        else:
            event.widget.itemconfigure(tk.CURRENT, fill="blue")
            self.master.update()
            time.sleep(.1)

# Importing TAF ############

    def readTAF(self):
        try:
            self.deletePoints()
        except:
            pass

        _id = self.sitepick.get()

        try:
            if self.saved[_id] == 1:
                print "ALREADY SAVED"
                print "Reading...", tafout + 'TAF.' + _id
                log = open(tafout + 'TAF.' + _id, 'r')
        except:
            print "NOPE NOT SAVED YET"
            print "Reading...", tafdir2
            cmd = 'textdb -r CRWTAF' + _id[1:] + ' >' + tafdir2
            print cmd
            os.system(cmd)
            try:
                log = open(tafdir2, 'r')
            except:
                print "Could not open " + tafdir2
                self.plotTAF()
                self.plotTAF_vis()
                return

        self.taf = Ddict(dict)
        lines = log.readlines()
        self.site = ''
        found = 0
        for line in lines:
            # print line
            test = re.match('FTUS', line)
            print line
            print test
            if test == None:
                line = line.strip()
                t = re.findall(_id, line.upper())
                if t:
                    found = 1
                if found == 1:
                    cig = self.detCig(line)
                    end = re.findall('=', line.upper())
        log.close()

        self.plotTAF()
        self.plotTAF_vis()
        return

    def plotTAF(self):
        _id = self.sitepick.get()
        print self.taf[_id]
        for index, i in enumerate(self.taf[_id]['fxtime']):
            temptime = self.taf[_id]['fxtime'][index]
            try:
                x, y = temptime, float(self.taf[_id]['cig'][index][0])
            except:
                x, y = temptime, float('150')

            x1, y1 = self.toGraphCoordfromTAF(x, y)
            x1 = pct_width_laxis * width + x1
            y1 = y1 - pct_bot * height + pct_top * height

            points.append(x1)
            points.append(y1)
            self.c.create_oval(x1 - 4, y1 - 4, x1 + 4, y1 + 4, fill=dot_color, tag="Ceiling")

        self.drawLine()
        return points

    def plotTAF_vis(self):
        _id = self.sitepick.get()

        for index, i in enumerate(self.taf[_id]['fxtime']):
            x, y = self.taf[_id]['fxtime'][index], float(self.taf[_id]['vis'][index])
            x1, y1 = self.toGraphCoordfromTAF_vis(x, y)
            x1 = pct_width_laxis * width + x1

            points.append(x1)
            points.append(y1)
            self.cv.create_oval(x1 - 4, y1 - 4, x1 + 4, y1 + 4, fill=dot_color, tag="Visibility")

        self.drawVisLine()
        self.c.tag_raise("Ceiling")
        return points

    def detCig(self, line):
        if re.match("FM|K\w{3}|TEMPO", line):
            pass
        else:
            return

        date = re.search('\d{6}Z (\d{2})(\d{2})\/(\d{2})(\d{2})', line.upper())
        if date:
            # 24 hours from now
            (_year, _month, _day, _hour, _min, _sec, _wday, _yday, _dst) = time.gmtime(time.mktime(time.gmtime()) + 86400)

            self.end_day = str(self.lt10(_day))
            self.end_month = str(self.lt10(_month))
            self.end_year = str(_year)
            YYYYmm = self.end_year + self.end_month

            # HHMM
            self.tafend_group = date.group(3) + date.group(4)
            self.tafbegin_group = date.group(1) + date.group(2)
            tafend = time.strptime(YYYYmm + self.tafend_group, "%Y%m%d%H")

            self.tafbegin = time.gmtime(time.mktime(tafend) - 86400)
            self.begin_day = str(self.lt10(self.tafbegin[2]))
            self.begin_month = str(self.lt10(self.tafbegin[1]))
            self.begin_year = str(self.tafbegin[0])

        t = re.findall('(\d{6})Z', line.upper())
        ttime = re.findall('FM(\d{6})', line.upper())
        tempo = re.findall('TEMPO (\d{4})\/(\d{4})', line.upper())
        # c=re.findall('(VV\d{3})|(FEW\d{3})|(SCT\d{3})|(BKN\d{3})|(OVC\d{3})',line.upper())
        c = re.findall('VV(\d{3})|BKN(\d{3})|OVC(\d{3})', line.upper())
        v = re.findall('(P\d)SM|(\d\d)SM|(\d)SM|(M1\/4)SM|(\d\/\d)SM|(\d \d\/\d)SM/', line.upper())
        w = re.findall('(\d{5})KT|(\d{5})G(\d+)KT', line.upper())

        if t:
            ti = self.tafbegin_group  # t[0][0:4]
            hour_fm_tafbegin = (time.mktime(
                time.strptime(self.begin_year + self.begin_month + self.lt10(ti), "%Y%m%d%H")) - time.mktime(
                time.strptime(self.begin_year + self.begin_month + self.tafbegin_group, "%Y%m%d%H"))) / 3600

            stn = re.findall('(K\w{3}) ', line.upper())
            self.site = stn[0]
            self.taf[self.site] = Ddict(dict)
            self.taf[self.site]['fxtime'] = [hour_fm_tafbegin]
            self.taf[self.site]['cig'] = []
            self.taf[self.site]['vis'] = []
            self.taf[self.site]['wnd'] = []


        if ttime:

            hour_fm_tafbegin = (time.mktime(
                time.strptime(self.begin_year + self.begin_month + ttime[0][0:4], "%Y%m%d%H")) - time.mktime(
                time.strptime(self.begin_year + self.begin_month + self.tafbegin_group, "%Y%m%d%H"))) / 3600

            if abs(hour_fm_tafbegin) > 24:
                hour_fm_tafbegin = (time.mktime(
                    time.strptime(self.end_year + self.end_month + ttime[0][0:4], "%Y%m%d%H")) - time.mktime(
                    time.strptime(self.begin_year + self.begin_month + self.tafbegin_group, "%Y%m%d%H"))) / 3600
            if hour_fm_tafbegin > 2:
                self.taf[self.site]['fxtime'].append(hour_fm_tafbegin - 1)
            else:
                self.taf[self.site]['fxtime'].append(hour_fm_tafbegin)

            # if tempo:
            # self.taf[self.site]['fxtime'].append([tempo[0][0]+'00',tempo[0][1]+'00'])

        tempcig = []
        for ceiling in c:
            if len(tempcig) >= 1:
                break
            for cig in ceiling:
                if cig != '':
                    tempcig.append(cig)

        if len(tempcig) == 0:
            tempcig.append("")
        try:
            self.taf[self.site]['cig'].append(tempcig)
        except:
            pass

        for visibility in v:
            for vis in visibility:
                if vis != '':
                    self.taf[self.site]['vis'].append(_ValidVsby[vis])

        for wind in w:
            for wnd in wind:
                if wnd != '':
                    self.taf[self.site]['wnd'].append(wnd)
        return


root = tk.Tk()
root.title("Draw Your TAF!")
CanvasDnD(root).grid(row=0, column=0)
root.mainloop()
