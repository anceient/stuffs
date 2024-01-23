import winreg
import json
import ctypes
import sys
import os
import dearpygui.dearpygui as dpg

###################################################################
#========================Console functions========================#
###################################################################

def print_console(inp,color=[255,255,255],console_window='conwin'):
    lastline = dpg.add_text(inp,wrap=dpg.get_item_width("conwin"), parent=console_window)
    dpg.configure_item(lastline,color=color)
    dpg.set_y_scroll(console_window, (dpg.get_y_scroll_max(console_window)+1)*1000000)

#############################################################################
#========================Winreg/resoulition checking========================#
#############################################################################

class registry:
    """
    class for handleing registry loading and logging.\n
    see get() for loading.
    """
    def __init__(self):
        self.list=[] #This is the list the log info will be stored in
        self.soft=None #init the soft/key values for winreg
        self.key=None
    
    def get(self,keys:dict={'Default Theme':'gold','Tooltips':'True'},location:list=[r'SOFTWARE\\','retardsinc\\pytemplate']):
        """
        Loads a given registry location and returns [keys:dict,ids:list]\n
        keys:dict a dict containing an id and a default value for that id,
        if the id is not in the registry then it will be made with your default.\n
        Location:list a list containing 2 strings the first you dont need to change,
        the second should be that path to your registry.
        """
        self.soft = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,location[0])
        self.key = winreg.CreateKey(self.soft,location[1])
        ids=[]
        [ids.append(i) for i in keys]

        for i in range(len(keys)):
            try:
                x=winreg.EnumValue(self.key,i)
                keys[i] = x
                self.list.append([ids[i],'loaded'])
            except Exception as e:
                if 'No more data is available' in str(e): self.list.append([ids[i],'created'])
                else: self.list.append([ids[i],'error'])
                winreg.SetValueEx(self.key,ids[i],0,winreg.REG_SZ,keys[ids[i]])
        return keys,ids

    def print_log_terminal(self):
        [print(i) for i in self.list]
    
    def print_log(self,console_window:str='conwin'):
        for i in self.list:
            if i[1]=='loaded': print_console(f'Loaded registry: {i[0]}.',color=[0,255,0],console_window=console_window)
            elif i[1]=='created': print_console(f'Created registry: {i[0]}.',color=[0,255,255],console_window=console_window)
            elif i[1]=='errored': print_console(f'Registry error: {i[0]}.',color=[255,0,0],console_window=console_window)

is_4k_monitor = False #This varabial only exists because when windows scales up a program for a 4k monitor it fuckes up our custom menubar dragging system
#so the fix is to just disable menubar dragging and reenable the default windows decorator(the bar at the top of a window that has the x button in it)
#2560 1440 2k
#3840 2160 4k
#2149 1234 ajk
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
if screensize == (2194 ,1234) or screensize == (3840,2160):
    is_4k_monitor = True

#############################################################################
#==============================File handleing===============================#
#############################################################################

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def loadfiles(files={'Themes':['json/themes.json','./themes.json']}):

    for i in files:
        temppath = resource_path(files[i][0]) if not os.path.isfile(files[i][1]) else files[i][1]
        tempfi = open(temppath)
        tempjson = json.load(tempfi)
        files[i]=[tempfi,tempjson,files[i][1]]
    return files

def localfilegen(sender,app_data,user_data):
    if not os.path.isfile(user_data[0]):
        with open(user_data[0],'w') as wfile:
            user_data[1].seek(0)
            wfile.write(str(user_data[1].read()))


#############################################################################
#==========================Window dragging callbacks========================#
#############################################################################

is_menu_bar_clicked = False

def add_menubar_drag():
    if is_4k_monitor == True:
        return None
    def mouse_click_callback():
        try:
            global is_menu_bar_clicked
            is_menu_bar_clicked = True if dpg.get_mouse_pos(local=False)[1] < 30 else False # 30 pixels is slightly more than the height of the default menu bar 
        except:
            pass
    def mouse_drag_callback(_, app_data): # functions for window draging
        try:
            if is_menu_bar_clicked:
                _, drag_delta_x, drag_delta_y = app_data
                viewport_pos_x, viewport_pos_y = dpg.get_viewport_pos()
                new_pos_x = viewport_pos_x + drag_delta_x
                new_pos_y = max(viewport_pos_y + drag_delta_y, 0)
                dpg.set_viewport_pos([new_pos_x, new_pos_y])
        except:
            pass
    with dpg.handler_registry() as hndlreg: #function so we can drag the top of the window
        dpg.add_mouse_click_handler(button=0, callback=mouse_click_callback)
        dpg.add_mouse_drag_handler(button=0, threshold=0, callback=mouse_drag_callback)

#############################################################################
#=================================Auto align================================#
#############################################################################

def auto_align(item, alignment_type: int, x_align: float = 0.5, y_align: float = 0.5):
    def _center_h(_s, _d, data):
        parent = dpg.get_item_parent(data[0])
        while dpg.get_item_info(parent)['type'] != "mvAppItemType::mvWindowAppItem":
            parent = dpg.get_item_parent(parent)
        parent_width = dpg.get_item_rect_size(parent)[0]
        width = dpg.get_item_rect_size(data[0])[0]
        new_x = (parent_width // 2 - width // 2) * data[1] * 2
        dpg.set_item_pos(data[0], [new_x, dpg.get_item_pos(data[0])[1]])

    def _center_v(_s, _d, data):
        parent = dpg.get_item_parent(data[0])
        while dpg.get_item_info(parent)['type'] != "mvAppItemType::mvWindowAppItem":
            parent = dpg.get_item_parent(parent)
        parent_width = dpg.get_item_rect_size(parent)[1]
        height = dpg.get_item_rect_size(data[0])[1]
        new_y = (parent_width // 2 - height // 2) * data[1] * 2
        dpg.set_item_pos(data[0], [dpg.get_item_pos(data[0])[0], new_y])

    if 0 <= alignment_type <= 2:
        with dpg.item_handler_registry():
            if alignment_type == 0:
                # horizontal only alignment
                dpg.add_item_visible_handler(callback=_center_h, user_data=[item, x_align])
            elif alignment_type == 1:
                # vertical only alignment
                dpg.add_item_visible_handler(callback=_center_v, user_data=[item, y_align])
            elif alignment_type == 2:
                # both horizontal and vertical alignment
                dpg.add_item_visible_handler(callback=_center_h, user_data=[item, x_align])
                dpg.add_item_visible_handler(callback=_center_v, user_data=[item, y_align])

        dpg.bind_item_handler_registry(item, dpg.last_container())

#############################################################################
#=============================Theme/font stuff==============================#
#############################################################################
def set_theme(current_theme=None):
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 140, 23), category=dpg.mvThemeCat_Core) #This is kinda pointless as we dont use the thing this controls
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1.5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 3, category=dpg.mvThemeCat_Core)

            dpg.add_theme_color(dpg.mvThemeCol_WindowBg,current_theme["background"])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive,current_theme["background"])
            dpg.add_theme_color(dpg.mvThemeCol_Button,current_theme["button"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,current_theme["buttonHover"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,current_theme["buttonActive"])
            #stuff for menu bar
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg,current_theme["background"])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg,current_theme["background"])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,current_theme["buttonHover"])
            dpg.add_theme_color(dpg.mvThemeCol_Header,current_theme["buttonActive"])
            #stuff for sliders
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,current_theme["buttonActive"])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive,current_theme["buttonHover"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,current_theme["button"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,current_theme["button"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive,current_theme["button"])
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding,8)
        
        with dpg.theme_component(dpg.mvCheckbox):
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark,current_theme["checkMarkColor"])
            dpg.add_theme_color(dpg.mvThemeCol_Border,current_theme["checkBoxBorder"])
        
        with dpg.theme_component(dpg.mvCheckbox,enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark,current_theme["buttonDisabledText"])
            dpg.add_theme_color(dpg.mvThemeCol_Border,current_theme['disabledBorder'])
            dpg.add_theme_color(dpg.mvThemeCol_Text,current_theme['disabledText'])
        
        with dpg.theme_component(dpg.mvRadioButton):
            dpg.add_theme_color(dpg.mvThemeCol_Border,current_theme['checkBoxBorder'])
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark,current_theme['checkMarkColor'])
        
        with dpg.theme_component(dpg.mvRadioButton,enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark,current_theme["buttonDisabledText"])
            dpg.add_theme_color(dpg.mvThemeCol_Border,current_theme['disabledBorder'])
            dpg.add_theme_color(dpg.mvThemeCol_Text,current_theme['disabledText'])
        
        with dpg.theme_component(dpg.mvInputInt,enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Border,current_theme['disabledBorder'])
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow,current_theme['disabledBorder'])
            dpg.add_theme_color(dpg.mvThemeCol_Text,current_theme['disabledText'])

        with dpg.theme_component(dpg.mvButton, enabled_state=False): # Disabled Button coloring
            dpg.add_theme_color(dpg.mvThemeCol_Button,current_theme["buttonDisabled"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,current_theme["buttonDisabled"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,current_theme["buttonDisabled"])
            dpg.add_theme_color(dpg.mvThemeCol_Text,current_theme["buttonDisabledText"])

        with dpg.theme_component(dpg.mvTooltip):
            dpg.add_theme_color(dpg.mvThemeCol_Border,current_theme["text_color1"])
            dpg.add_theme_color(dpg.mvThemeCol_Text,current_theme["text_color1"])
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,64)
    dpg.bind_theme(global_theme)
    global closebtn,minimizebtn
    with dpg.theme() as closebtn:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign ,1.00,category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button,[0,0,0,0])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,[255,0,0,155])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,[0,0,0,0])
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0, category=dpg.mvThemeCat_Core)

    with dpg.theme() as minimizebtn:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign ,1.00,category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button,[0,0,0,0])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,[255,255,255,155])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,[0,0,0,0])
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0, category=dpg.mvThemeCat_Core)

#############################################################################
#=====================window buttons/viewport sizeing=======================#
#############################################################################

def add_window_buttons(font=None):
    if is_4k_monitor == True:
        return None
    dpg.add_button(label='X',tag='closebtn',callback=lambda: os._exit(0))
    dpg.add_button(label='-',tag='minbtn',callback=lambda: dpg.minimize_viewport())
    dpg.bind_item_theme('closebtn',closebtn)
    dpg.bind_item_theme('minbtn',minimizebtn)
    auto_align('closebtn', 0, x_align=1, y_align=0.1)
    #auto_align(item tag,int alignment mode 0 1 or 2, x_align=0 to 1, y_align=0 to 1)
    dpg.bind_item_font('minbtn',font)

def update_window_btns_pos():
    if is_4k_monitor == True:
        return None
    cx, _ = dpg.get_item_pos('closebtn')
    if cx > dpg.get_viewport_width():
        dpg.set_item_pos('closebtn',[0,0])
        dpg.set_item_pos('minbtn',[0,0])
    dpg.set_item_pos('minbtn',[cx-26,0])

def update_viewport_size():
    if is_4k_monitor == True:
        return None
    w,h = dpg.get_item_width('primary'),dpg.get_item_height('primary')
    dpg.set_viewport_width(w)
    dpg.set_viewport_height(h)
    dpg.set_item_pos('primary',[0,0])