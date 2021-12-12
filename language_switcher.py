# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy, os

def get_dir(file_name):
    script_file = os.path.realpath(__file__)
    dir = os.path.dirname(script_file)
    dir = os.path.join(dir, file_name)
    return dir

def get_languages():
    dir = get_dir("languages")
    languages = []
    f = open(dir, "r")
    for line in f:
        line = line.strip()
        if line[0]=='#':
            continue
        if line[-1]==":":
            continue
        list = line.split(":")
        enum_item = (list[2], list[1], list[2], int(list[0]))
        languages.append(enum_item)
    
    languages.sort(key=lambda x: x[-1])
    
    return languages

def load_user_pref_lang(context):
    dir = get_dir("user_pref_lang.txt")
    
    f = open(dir, "r")
    if not f:
        return

    pref = context.preferences.addons['LanguageSwitcher'].preferences
    pref.lang_stack.clear()
    for line in f:
        line = line.strip()
        # print(line)
        item = pref.lang_stack.add()
        item.lang = line
    
    f.close()

def update_user_pref_lang(context):
    dir = get_dir("user_pref_lang.txt")

    f = open(dir, "w")
    pref = context.preferences.addons['LanguageSwitcher'].preferences
 
    for i in pref.lang_stack:
        f.write(i.lang+"\n")
    
    f.close()
    
def lang_enum_update(self, context):
    update_user_pref_lang(context)

class LS_OT_switch(bpy.types.Operator):
    bl_idname='view3d.language_switcher_switch'
    bl_label='Switch'
    bl_options = {'UNDO'}
    
    def execute(self, context):
        pref = context.preferences.addons['LanguageSwitcher'].preferences
        
        index = pref.act_idx
        index +=1
        
        count = len(pref.lang_stack)
        index %= count
        
        pref.act_idx = index
        
        context.preferences.view.language = pref.lang_stack[index].lang
        
        return {'FINISHED'}
    
class LS_OT_add_lang(bpy.types.Operator):
    bl_idname='language_switcher.add_lang'
    bl_label='Add Language'
    bl_options = {'UNDO','INTERNAL'}
    
    def execute(self, context):
        pref = context.preferences.addons['LanguageSwitcher'].preferences
        
        item = pref.lang_stack.add()

        update_user_pref_lang(context)
        
        return {'FINISHED'}

class LS_OT_remove_lang(bpy.types.Operator):
    bl_idname='language_switcher.remove_lang'
    bl_label='Remove Language'
    bl_options = {'UNDO','INTERNAL'}
    
    @classmethod
    def poll(cls, context):
        pref = context.preferences.addons['LanguageSwitcher'].preferences
        return pref.lang_stack
    
    def execute(self, context):
        pref = context.preferences.addons['LanguageSwitcher'].preferences
        
        index = pref.act_idx
        
        pref.lang_stack.remove(index)
        pref.act_idx = index-1
        
        context.preferences.view.language = pref.lang_stack[pref.act_idx].lang
        update_user_pref_lang(context)

        return {'FINISHED'}

class LS_OT_move(bpy.types.Operator):
    bl_idname = 'language_switcher.move'
    bl_label = 'Move'
    bl_options = {'UNDO','INTERNAL'}
    
    direction: bpy.props.BoolProperty(name = 'move_direction') #True:UP; False:DOWN
    
    @classmethod
    def poll(cls, context):
        pref = context.preferences.addons['LanguageSwitcher'].preferences
        return pref.lang_stack
    
    def execute(self, context):
        pref = context.preferences.addons['LanguageSwitcher'].preferences
        index = pref.act_idx
        max_index = len(pref.lang_stack)-1
        
        if self.direction: #UP
            if index ==0:
                return {'FINISHED'}
            else:
                neightbor = index-1
        else: #DOWN
            if index==max_index:
                return {'FINISHED'}
            else:
                neightbor = index+1
        
        pref.lang_stack.move(neightbor, index)
        pref.act_idx = neightbor

        update_user_pref_lang(context)

        return {'FINISHED'}

class LS_UL_uilist(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split=layout.split(factor=0.5)
            split.label(text=item.lang)
            split.prop(item, 'lang', text='')
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

LANGUAGES = get_languages()
class LS_stack(bpy.types.PropertyGroup):
    lang: bpy.props.EnumProperty(items=LANGUAGES, update = lang_enum_update)
    
class LanguageSwitcherPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    
    lang_stack: bpy.props.CollectionProperty(type=LS_stack)
    act_idx: bpy.props.IntProperty(default=0, min=0)
    use_ui_button: bpy.props.BoolProperty(default=True)

    def draw(self, context):
        layout=self.layout
        
        row = layout.row()
        row.prop(self, 'use_ui_button', text = 'Use UI Button')

        row = layout.row()
        row.template_list('LS_UL_uilist','',self, 'lang_stack', self, 'act_idx')
        
        subcol = row.column(align = True)
        subcol.operator('language_switcher.add_lang',text = '', icon = 'ADD')
        subcol.operator('language_switcher.remove_lang',text = '', icon = 'REMOVE')
        
        subcol.separator()
        subcol.operator('language_switcher.move',text = '', icon = 'TRIA_UP').direction = True #UP
        subcol.operator('language_switcher.move',text = '', icon = 'TRIA_DOWN').direction = False #DOWN


def LS_header(self, context):
    ad = context.preferences.addons.get('LanguageSwitcher')
    if not ad:
        return
    pref = ad.preferences
    if not pref.lang_stack:
        return
    if not pref.use_ui_button:
        return
    lang = pref.lang_stack[pref.act_idx].lang
    display_lang = context.preferences.view.language
    self.layout.operator('view3d.language_switcher_switch', text=display_lang)

classes=[
    LS_stack,
    
    LS_OT_add_lang,
    LS_OT_remove_lang,
    LS_OT_move,
    LS_OT_switch,
    
    LS_UL_uilist,
    LanguageSwitcherPreferences,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
        
    load_user_pref_lang(bpy.context)
    
    bpy.types.VIEW3D_HT_tool_header.append(LS_header)
    
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
        
    bpy.types.VIEW3D_HT_tool_header.remove(LS_header)

#if __name__ == "__main__":
#    register()
