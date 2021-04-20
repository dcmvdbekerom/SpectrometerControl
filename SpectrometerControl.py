import tkinter as tk
import tkinter.ttk as ttk
from tkinter import ACTIVE, DISABLED
from tkinter.messagebox import showerror, askokcancel
from serial.tools.list_ports import comports
import serial


class Serial(serial.Serial):
    def query(self, s):
        self.write(s.encode())
        self.readline()
        return self.readline().decode().rstrip()


def changeWavelength(event=None):
    la_swl['text'] = 'Working...'
    wl = float(en_gwl.get())
    ser.query('GOWAVE {:.3f}\n'.format(wl))
    wl_str = ''
    while wl_str == '':
        wl_str = ser.query('WAVE?\n')
    set_wl = float(wl_str)
    
    en_swl['state'] = ACTIVE
    en_swl.delete(0,tk.END)
    en_swl.insert(0,'{:.3f}'.format(set_wl))
    en_swl['state'] = DISABLED
    la_swl['text'] = ''


def changeGrating(event=None):
    la_swl['text'] = 'Working...'
    i_grating = cb_gr.current() + 1
    ser.query('GRAT {:1d}\n'.format(i_grating))
    changeWavelength()
    la_swl['text'] = ''


def openEditGratingWindow(event=None):
    i_grating = int(ser.query('GRAT?\n')[0])
    lines = ser.query('GRAT{:1d}LINES?\n'.format(i_grating))
    label = ser.query('GRAT{:1d}LABEL?\n'.format(i_grating))

    editwin = tk.Toplevel(root)
    editwin.title("Grating {:1d}".format(i_grating))

    la0 = ttk.Label(editwin, text="Enter new values for grating {:1d}:".format(i_grating))
    la0.grid(row=0, column=0, columnspan=2)

    ttk.Label(editwin, text="Lines mm-1:").grid(row=1, column=0)
    en0 = ttk.Entry(editwin)
    en0.insert(0,lines)
    en0.grid(row=1, column=1)
    
    ttk.Label(editwin, text="Label:").grid(row=2, column=0)
    en1 = ttk.Entry(editwin)
    en1.insert(0,label)
    en1.grid(row=2,column=1)

    def saveGratingParams(event=None):
        lines = en0.get()[:4]
        label = en1.get()[:7]

        message = '\n'.join(['Lines mm-1: \t' + lines,
                             'Label: \t\t' + label,
                             '\nAre you sure?'])
        if(askokcancel(
            title='Confirmation',
            message=message)):

            ser.query('GRAT{:1d}LINES {:s}\n'.format(i_grating,lines))
            ser.query('GRAT{:1d}LABEL {:s}\n'.format(i_grating,label))
            gratings = list(cb_gr['values'])
            gratings[i_grating-1] = '{:1d}. {:s} mm-1 {:s}'.format(
                i_grating, lines, label)
            cb_gr['values'] = gratings
            cb_gr.delete(0,tk.END)
            cb_gr.insert(0,gratings[i_grating-1])

            editwin.destroy()

    bt_edit = ttk.Button(editwin, text='Store', command=saveGratingParams)
    bt_edit.grid(row=3, column=1)
    
    
def openConnectionWindow(event=None):
    conwin = tk.Toplevel(root)
    conwin.title("Connection")

    ttk.Label(conwin, text="Baud:").grid(row=0, column=0)
    cbx0 = ttk.Combobox(conwin, values=[1200,
                                        2400,
                                        4800,
                                        9600,
                                        19200,
                                        38400,
                                        115200])
    cbx0.current(3)
    cbx0.grid(row=0, column=1)

    ttk.Label(conwin, text="Data bits:").grid(row=1, column=0)
    cbx1 = ttk.Combobox(conwin, values=[5, 6, 7, 8])
    cbx1.current(3)
    cbx1.grid(row=1, column=1)

    ttk.Label(conwin, text="Stop bits:").grid(row=2, column=0)
    cbx2 = ttk.Combobox(conwin, values=[1, 2])
    cbx2.current(0)
    cbx2.grid(row=2, column=1)

    ttk.Label(conwin, text="Parity:").grid(row=3, column=0)
    cbx3 = ttk.Combobox(conwin,
                        values=['None', 'Even', 'Odd', 'Mark', 'Space'])
    cbx3.current(0)
    cbx3.grid(row=3, column=1)

    ttk.Label(conwin, text="Timeout (ms):").grid(row=4, column=0)
    cbx4 = ttk.Entry(conwin)
    cbx4.insert(0, '2000')
    cbx4.grid(row=4, column=1)

    def connectComPort():
        la_swl['text'] = 'Working...'
        ser.port = cb_com.get().split()[0]
        ser.baudrate = int(cbx0.get())
        ser.bytesize = int(cbx1.get())
        ser.stopbits = int(cbx2.get())
        ser.parity = cbx3.get()[0]
        ser.timeout = float(cbx4.get())/1e3

        try:
            ser.open()
            cb_com['state'] = DISABLED
            bt_com['state'] = ACTIVE
            cb_gr['state'] = ACTIVE
            bt_gr['state'] = ACTIVE
            en_gwl['state'] = ACTIVE
            bt_gwl['state'] = ACTIVE
            
            root.title(ser.query('INFO?\n'))
            
            gratings = []
            for i in range(3):
                i_str = '{:1d}'.format(i+1)
                gratings.append(i_str + '. ')
                gratings[-1] += ser.query('GRAT'+i_str+'LINES?\n')
                gratings[-1] += ' mm-1 '
                gratings[-1] += ser.query('GRAT'+i_str+'LABEL?\n')

            cb_gr['values'] = gratings
            i_grating = int(ser.query('GRAT?\n')[0])
            cb_gr.current(i_grating - 1)

            wl = float(ser.query('WAVE?\n'))
            en_gwl.insert(0,'{:.3f}'.format(wl))
            en_swl['state'] = ACTIVE
            en_swl.insert(0,'{:.3f}'.format(wl))
            en_swl['state'] = DISABLED
            

        except(serial.serialutil.SerialException):
            showerror(title='Connection error',
                      message='Port already in use!')

        conwin.destroy()
        la_swl['text'] = ''

    bt0 = ttk.Button(conwin, text='Connect', command=lambda: connectComPort())
    bt0.grid(row=5, column=1)


def disconnectComPort():
    la_swl['text'] = 'Working...'
    ser.close()
    cb_com['state'] = ACTIVE
    bt_com['state'] = DISABLED
    cb_gr['state'] = DISABLED
    bt_gr['state'] = DISABLED
    en_gwl['state'] = DISABLED
    bt_gwl['state'] = DISABLED
    root.title('<<Disconnected>>')
    cb_com['values'] = comports()
    la_swl['text'] = ''


ser = Serial()
root = tk.Tk()
root.title('<<Disconnected>>')

# Serial connection
la_com = ttk.Label(root, text='Port:')
la_com.grid(row=0, column=0)

cb_com = ttk.Combobox(root, values=comports())
cb_com.grid(row=0, column=1)

bt_com = ttk.Button(text='Disconnect', state=DISABLED,
                    command=disconnectComPort)
bt_com.grid(row=0, column=2)

# Grating
la_gr = ttk.Label(text='Grating:')
la_gr.grid(row=1, column=0)

cb_gr = ttk.Combobox(root, state=DISABLED)
cb_gr.grid(row=1, column=1)

bt_gr = ttk.Button(text='Edit', state=DISABLED, command=openEditGratingWindow)
bt_gr.grid(row=1, column=2)

# Wavelength
la_gwl = ttk.Label(text='Goto WL:')
la_gwl.grid(row=2, column=0)

en_gwl = ttk.Entry(state=DISABLED)
en_gwl.grid(row=2, column=1)

bt_gwl = ttk.Button(text='GO', state=DISABLED, command=changeWavelength)
bt_gwl.grid(row=2, column=2)

la_swl = ttk.Label(text='Set WL:')
la_swl.grid(row=3, column=0)

en_swl = ttk.Entry()
en_swl['state'] = DISABLED
en_swl.grid(row=3, column=1)

la_swl = ttk.Label()
la_swl.grid(row=3, column=2)

# assign function to combobox
cb_com.bind('<<ComboboxSelected>>', openConnectionWindow)
cb_gr.bind('<<ComboboxSelected>>', changeGrating)

root.mainloop()
ser.close()
