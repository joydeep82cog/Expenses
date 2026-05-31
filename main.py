# Expense Tracking App (Kivy)
# Main entry point

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, StringProperty
from models import Expense
from utils import calculate_settlement, save_settlement_to_excel, load_trip_from_excel
import os
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.image import Image
import io
from kivy.core.image import Image as CoreImage
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False

TRIP_ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), 'Trip Archive')

# On Android, use the app's user-data directory for writable storage
try:
    from android.storage import app_storage_path  # type: ignore
    TRIP_ARCHIVE_DIR = os.path.join(app_storage_path(), 'Trip Archive')
except ImportError:
    pass  # Not on Android – use local path

if not Builder.files:
    Builder.load_file(os.path.join(os.path.dirname(__file__), 'expense.kv'))
else:
    kv_path = os.path.join(os.path.dirname(__file__), 'expense.kv')
    if kv_path not in Builder.files:
        Builder.load_file(kv_path)


def focus_next_widget(fields, current):
    """Move focus to the next field in the list (wraps around)."""
    try:
        idx = fields.index(current)
        next_field = fields[(idx + 1) % len(fields)]
        next_field.focus = True
    except (ValueError, AttributeError):
        pass


def focus_prev_widget(fields, current):
    """Move focus to the previous field in the list (wraps around)."""
    try:
        idx = fields.index(current)
        prev_field = fields[(idx - 1) % len(fields)]
        prev_field.focus = True
    except (ValueError, AttributeError):
        pass


class ParticipantsScreen(Screen):
    participants = ListProperty([])

    def _tab_fields(self):
        return [self.ids.trip_name_input, self.ids.participant_input]

    def on_pre_enter(self):
        self.update_participants_list()
        Window.bind(on_key_down=self._on_key_down)

    def on_pre_leave(self):
        Window.unbind(on_key_down=self._on_key_down)

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        fields = self._tab_fields()
        focused = next((f for f in fields if f.focus), None)
        if focused is None:
            return False
        if key == 9:
            if 'shift' in modifiers:
                focus_prev_widget(fields, focused)
            else:
                focus_next_widget(fields, focused)
            return True
        return False

    def add_participant(self, name):
        name = name.strip()
        if not name:
            self.show_toast('Please enter a name!')
            return
        if name in self.participants:
            self.show_toast(f'{name} is already added!')
            return
        self.participants.append(name)
        self.ids.participant_input.text = ''
        self.update_participants_list()

    def update_participants_list(self):
        box = self.ids.participants_list
        box.clear_widgets()
        for p in self.participants:
            lbl = Label(text=p, color=(0.96, 0.96, 0.86, 1), font_size=18,
                        size_hint_y=None, height=40)
            box.add_widget(lbl)

    def load_trip(self):
        try:
            if not os.path.exists(TRIP_ARCHIVE_DIR):
                os.makedirs(TRIP_ARCHIVE_DIR)
            files = sorted([f for f in os.listdir(TRIP_ARCHIVE_DIR) if f.endswith('.xlsx')])
        except Exception as e:
            self.show_toast(f'Cannot access archive folder: {str(e)}')
            return

        from kivy.uix.scrollview import ScrollView

        popup_ref = [None]  # always defined before use

        outer = BoxLayout(orientation='vertical', spacing=6, padding=8)

        if not files:
            outer.add_widget(Label(
                text='No archived trips found.\nArchive a trip first using\n"Settle & Archive".',
                color=(0.96, 0.96, 0.86, 1), font_size=18,
                bold=True, halign='center', valign='middle',
                size_hint_y=None, height=120
            ))
        else:
            scroll = ScrollView(size_hint=(1, 1))
            inner = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
            inner.bind(minimum_height=inner.setter('height'))

            def make_load_fn(fp, popup_holder):
                def do_load(inst):
                    try:
                        loaded_participants, loaded_expenses = load_trip_from_excel(fp)
                        self.participants = loaded_participants
                        expenses_screen = self.manager.get_screen('expenses')
                        expenses_screen.expenses = []
                        for row in loaded_expenses:
                            omitted = row['Omitted'].split(', ') if isinstance(row.get('Omitted'), str) and row.get('Omitted') else []
                            notes = str(row.get('Notes', '')) if row.get('Notes') else ''
                            expenses_screen.expenses.append(
                                Expense(row.get('Item', ''), row.get('Amount', 0), row.get('Paid By', ''), omitted, notes)
                            )
                        self.ids.trip_name_input.text = os.path.splitext(os.path.basename(fp))[0]
                        self.update_participants_list()
                        expenses_screen.update_expenses_list()
                        if popup_holder[0]:
                            popup_holder[0].dismiss()
                        self.show_toast('Trip loaded successfully!')
                    except Exception as e:
                        self.show_toast(f'Error loading: {str(e)}')
                return do_load

            def make_delete_fn(fp, fname, popup_holder):
                def do_delete(inst):
                    try:
                        os.remove(fp)
                        self.show_toast(f'Deleted: {fname}')
                        if popup_holder[0]:
                            popup_holder[0].dismiss()
                        Clock.schedule_once(lambda dt: self.load_trip(), 0.3)
                    except Exception as e:
                        self.show_toast(f'Error deleting: {str(e)}')
                return do_delete

            for fname in files:
                fp = os.path.join(TRIP_ARCHIVE_DIR, fname)
                row = BoxLayout(orientation='horizontal', size_hint_y=None, height=52, spacing=6)

                name_lbl = Button(
                    text=f'  {os.path.splitext(fname)[0]}',
                    background_normal='', background_color=(0.22, 0.27, 0.32, 1),
                    color=(0.96, 0.96, 0.86, 1), font_size=16, bold=True,
                    halign='left', valign='middle', size_hint_x=0.6
                )
                name_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
                name_lbl.bind(on_release=make_load_fn(fp, popup_ref))

                load_btn = Button(
                    text='Load', size_hint_x=0.2,
                    background_normal='', background_color=(0.95, 0.6, 0.1, 1),
                    color=(0.1, 0.1, 0.1, 1), font_size=15, bold=True
                )
                load_btn.bind(on_release=make_load_fn(fp, popup_ref))

                del_btn = Button(
                    text='Delete', size_hint_x=0.2,
                    background_normal='', background_color=(0.82, 0.18, 0.18, 1),
                    color=(1, 1, 1, 1), font_size=15, bold=True
                )
                del_btn.bind(on_release=make_delete_fn(fp, fname, popup_ref))

                row.add_widget(name_lbl)
                row.add_widget(load_btn)
                row.add_widget(del_btn)
                inner.add_widget(row)

            scroll.add_widget(inner)
            outer.add_widget(scroll)

        close_btn = Button(
            text='Close', size_hint_y=None, height=52,
            background_normal='', background_color=(0.95, 0.6, 0.1, 1),
            color=(0.1, 0.1, 0.1, 1), bold=True, font_size=18
        )
        outer.add_widget(close_btn)

        popup = Popup(title='Archived Trips', title_color=(1, 1, 1, 1),
                      content=outer, size_hint=(0.92, 0.85),
                      background_color=(0.18, 0.22, 0.25, 1))
        popup_ref[0] = popup
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def start_new_trip(self):
        self.participants = []
        self.ids.trip_name_input.text = ''
        self.update_participants_list()
        expenses_screen = self.manager.get_screen('expenses')
        expenses_screen.expenses = []
        expenses_screen.selected_index = None
        expenses_screen.update_expenses_list()
        self.show_toast('New trip started!')

    def show_toast(self, msg):
        layout = FloatLayout(size_hint=(None, None), size=(360, 50),
                             pos_hint={'center_x': 0.5, 'top': 0.98})
        with layout.canvas.before:
            Color(0.1, 0.1, 0.1, 0.88)
            self._toast_rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[10])
        lbl = Label(text=msg, color=(1, 1, 1, 1), bold=True, font_size=16, size_hint=(1, 1))
        layout.add_widget(lbl)
        layout.bind(pos=lambda inst, val: setattr(self._toast_rect, 'pos', val))
        layout.bind(size=lambda inst, val: setattr(self._toast_rect, 'size', val))
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self.remove_widget(layout), 2)

    def go_to_expenses(self):
        trip_name = self.ids.trip_name_input.text.strip()
        if not trip_name:
            self.show_toast('Please enter a trip name first!')
            return
        if not self.participants:
            self.show_toast('Please add at least one participant!')
            return
        self.manager.current = 'expenses'


class ExpensesScreen(Screen):
    """
    ExpensesScreen is a Kivy Screen for managing and displaying expenses in a group trip expense sharing app.
    Attributes:
        expenses (ListProperty): List of Expense objects representing all expenses added.
        selected_index (int or None): Index of the currently selected expense in the list, or None if none selected.
        _omitted_members (list): List of participant names to omit from the current expense.
    Methods:
        _tab_fields():
            Returns a list of input widgets for tab navigation (item, amount, notes).
        on_pre_enter():
            Prepares the screen before it is displayed, including updating participant lists and resetting fields.
        on_pre_leave():
            Cleans up when leaving the screen, such as unbinding keyboard events.
        _on_key_down(window, key, scancode, codepoint, modifiers):
            Handles keyboard navigation (Tab/Shift+Tab) between input fields.
        add_expense(item, amount, notes):
            Validates and adds a new expense to the list, updating the UI and clearing input fields.
        open_omit_popup():
            Opens a popup to select participants to omit from the current expense.
        show_toast(msg):
            Displays a temporary toast message at the top of the screen.
        update_expenses_list():
            Refreshes the displayed list of expenses, highlighting the selected one.
        select_expense(idx):
            Selects an expense by index and updates the UI.
        delete_selected_expense():
            Deletes the currently selected expense from the list.
        modify_selected_expense():
            Loads the selected expense into the input fields for editing and removes it from the list.
        go_to_settlement():
            Navigates to the settlement screen if there are expenses.
        go_back():
            Navigates back to the participants screen.
    """
    expenses = ListProperty([])
    selected_index = None
    _omitted_members = []

    def _tab_fields(self):
        return [self.ids.item_input, self.ids.amount_input, self.ids.notes_input]

    def on_pre_enter(self):
        participants = list(self.manager.get_screen('participants').participants)
        self.ids.paid_by_spinner.values = participants
        if self.ids.paid_by_spinner.text not in participants:
            self.ids.paid_by_spinner.text = participants[0] if participants else 'Paid by'
        self._omitted_members = []
        self.ids.omit_btn.text = 'Omit members (tap to select)'
        self.update_expenses_list()
        Window.bind(on_key_down=self._on_key_down)

    def on_pre_leave(self):
        Window.unbind(on_key_down=self._on_key_down)

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        fields = self._tab_fields()
        focused = next((f for f in fields if f.focus), None)
        if focused is None:
            return False
        if key == 9:  # Tab
            if 'shift' in modifiers:
                focus_prev_widget(fields, focused)
            else:
                focus_next_widget(fields, focused)
            return True
        return False

    def add_expense(self, item, amount, notes):
        try:
            trip_name = self.manager.get_screen('participants').ids.trip_name_input.text.strip()
            if not trip_name:
                self.show_toast('Please enter a trip name first!')
                return
            item = item.strip()
            if not item:
                self.show_toast('Please enter an expense item!')
                return
            if not amount or not amount.strip():
                self.show_toast('Please enter an amount!')
                return
            try:
                amount_val = float(amount)
            except ValueError:
                self.show_toast('Amount must be a valid number!')
                return
            if amount_val <= 0:
                self.show_toast('Amount must be greater than zero!')
                return
            paid_by = self.ids.paid_by_spinner.text.strip()
            participants = list(self.manager.get_screen('participants').participants)
            if not paid_by or paid_by.lower() == 'paid by' or paid_by not in participants:
                self.show_toast('Please select who paid!')
                return
            omitted_list = list(self._omitted_members)
            exp = Expense(item, amount_val, paid_by, omitted_list, notes.strip())
            self.expenses.append(exp)
            self.ids.item_input.text = ''
            self.ids.amount_input.text = ''
            self.ids.paid_by_spinner.text = participants[0] if participants else 'Paid by'
            self.ids.omit_btn.text = 'Omit members (tap to select)'
            self._omitted_members = []
            self.ids.notes_input.text = ''
            self.update_expenses_list()
            self.ids.item_input.focus = True
            self.show_toast('Expense added!')
        except Exception as e:
            self.show_toast(f'Error: {str(e)}')

    def open_omit_popup(self):
        participants = list(self.manager.get_screen('participants').participants)
        if not participants:
            self.show_toast('No participants to omit!')
            return
        from kivy.uix.checkbox import CheckBox
        from kivy.uix.scrollview import ScrollView

        item_text = self.ids.item_input.text
        amount_text = self.ids.amount_input.text
        notes_text = self.ids.notes_input.text

        outer = BoxLayout(orientation='vertical', spacing=6, padding=10)
        scroll = ScrollView(size_hint=(1, 1))
        inner = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        inner.bind(minimum_height=inner.setter('height'))

        checkboxes = {}
        for p in participants:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=48)
            cb = CheckBox(size_hint_x=None, width=48, active=(p in self._omitted_members))
            lbl = Label(text=p, color=(1, 1, 1, 1), font_size=18, bold=True,
                        halign='left', valign='middle')
            lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            row.add_widget(cb)
            row.add_widget(lbl)
            inner.add_widget(row)
            checkboxes[p] = cb

        scroll.add_widget(inner)
        outer.add_widget(scroll)

        done_btn = Button(text='Done – Add Expense', size_hint_y=None, height=52,
                          background_normal='',
                          background_color=(0.95, 0.6, 0.1, 1),
                          color=(0.1, 0.1, 0.1, 1),
                          bold=True, font_size=18)
        outer.add_widget(done_btn)

        popup = Popup(title='Select members to omit',
                      title_color=(1, 1, 1, 1),
                      content=outer,
                      size_hint=(0.88, 0.78),
                      background_color=(0.18, 0.22, 0.25, 1))

        def on_done(inst):
            self._omitted_members = [p for p, cb in checkboxes.items() if cb.active]
            if self._omitted_members:
                self.ids.omit_btn.text = f'Omit: {", ".join(self._omitted_members)}'
            else:
                self.ids.omit_btn.text = 'Omit members (tap to select)'
            popup.dismiss()
            self.add_expense(item_text, amount_text, notes_text)

        done_btn.bind(on_release=on_done)
        popup.open()

    def show_toast(self, msg):
        layout = FloatLayout(size_hint=(None, None), size=(360, 50),
                             pos_hint={'center_x': 0.5, 'top': 0.98})
        with layout.canvas.before:
            Color(0.1, 0.1, 0.1, 0.88)
            self._toast_rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[10])
        lbl = Label(text=msg, color=(1, 1, 1, 1), bold=True, font_size=16,
                    size_hint=(1, 1))
        layout.add_widget(lbl)
        layout.bind(pos=lambda inst, val: setattr(self._toast_rect, 'pos', val))
        layout.bind(size=lambda inst, val: setattr(self._toast_rect, 'size', val))
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self.remove_widget(layout), 2)

    def update_expenses_list(self):
        box = self.ids.expenses_list
        box.clear_widgets()
        ALT_A = (0.22, 0.27, 0.32, 1)
        ALT_B = (0.28, 0.34, 0.40, 1)
        SEL   = (0.15, 0.55, 0.25, 1)
        for idx, exp in enumerate(self.expenses):
            omit_str = f"  ✂ omit: {', '.join(exp.omitted)}" if exp.omitted else ''
            notes_str = f"  📝 {exp.notes}" if exp.notes else ''
            if idx == self.selected_index:
                bg_color = SEL
            elif idx % 2 == 0:
                bg_color = ALT_A
            else:
                bg_color = ALT_B
            btn = Button(
                text=f"  {idx+1}. {exp.item}  ₹{exp.amount:.2f}  by {exp.paid_by}{omit_str}{notes_str}",
                background_normal='', background_color=bg_color,
                color=(0.96, 0.96, 0.86, 1), font_size=15, bold=True,
                size_hint_y=None, height=52, halign='left', valign='middle'
            )
            btn.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            btn.bind(on_release=lambda inst, i=idx: self.select_expense(i))
            box.add_widget(btn)

    def select_expense(self, idx):
        self.selected_index = idx
        self.update_expenses_list()

    def delete_selected_expense(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.expenses):
            self.expenses.pop(self.selected_index)
            self.selected_index = None
            self.update_expenses_list()
            self.show_toast('Expense deleted!')
        else:
            self.show_toast('Please select an expense to delete!')

    def modify_selected_expense(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.expenses):
            exp = self.expenses[self.selected_index]
            self.ids.item_input.text = exp.item
            self.ids.amount_input.text = str(exp.amount)
            self.ids.paid_by_spinner.text = exp.paid_by
            self._omitted_members = list(exp.omitted)
            if self._omitted_members:
                self.ids.omit_btn.text = f'Omit: {", ".join(self._omitted_members)}'
            else:
                self.ids.omit_btn.text = 'Omit members (tap to select)'
            self.ids.notes_input.text = exp.notes
            self.expenses.pop(self.selected_index)
            self.selected_index = None
            self.update_expenses_list()
            self.show_toast('Edit the fields and press Add Expense to save.')
        else:
            self.show_toast('Please select an expense to modify!')

    def go_to_settlement(self):
        if not self.expenses:
            self.show_toast('Please add at least one expense!')
            return
        self.manager.current = 'settlement'

    def go_back(self):
        self.manager.current = 'participants'

    def select_expense(self, idx):
        self.selected_index = idx
        self.update_expenses_list()

    def delete_selected_expense(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.expenses):
            self.expenses.pop(self.selected_index)
            self.selected_index = None
            self.update_expenses_list()
            self.show_toast('Expense deleted!')
        else:
            self.show_toast('Please select an expense to delete!')

    def modify_selected_expense(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.expenses):
            exp = self.expenses[self.selected_index]
            self.ids.item_input.text = exp.item
            self.ids.amount_input.text = str(exp.amount)
            self.ids.paid_by_spinner.text = exp.paid_by
            self._omitted_members = list(exp.omitted)
            if self._omitted_members:
                self.ids.omit_btn.text = f'Omit: {", ".join(self._omitted_members)}'
            else:
                self.ids.omit_btn.text = 'Omit members (tap to select)'
            self.ids.notes_input.text = exp.notes
            self.expenses.pop(self.selected_index)
            self.selected_index = None
            self.update_expenses_list()
            self.show_toast('Edit the fields and press Add Expense to save.')
        else:
            self.show_toast('Please select an expense to modify!')

    def go_to_settlement(self):
        if not self.expenses:
            self.show_toast('Please add at least one expense!')
            return
        self.manager.current = 'settlement'

    def go_back(self):
        self.manager.current = 'participants'


class SettlementScreen(Screen):
    def on_pre_enter(self):
        try:
            participants = self.manager.get_screen('participants').participants
            expenses = self.manager.get_screen('expenses').expenses
            if not participants:
                return
            balances = calculate_settlement(participants, expenses)
            box = self.ids.settlement_list
            box.clear_widgets()
            all_settled = True
            for p, bal in balances.items():
                if abs(bal) < 0.01:
                    continue
                all_settled = False
                if bal > 0:
                    txt = f"{p}  RECEIVE: ₹{bal:.2f}"
                    bg = (0.2, 0.75, 0.4, 1)
                else:
                    txt = f"{p}  PAY: ₹{-bal:.2f}"
                    bg = (0.8, 0.3, 0.3, 1)
                btn = Button(text=txt, font_size=17, bold=True,
                             background_normal='', background_color=bg,
                             color=(1, 1, 1, 1), size_hint_y=None, height=44)
                box.add_widget(btn)
            if all_settled:
                box.add_widget(Label(text='All settled! No payments needed.',
                                     color=(0.96, 0.96, 0.86, 1), font_size=18,
                                     size_hint_y=None, height=44))
            self.show_pie_chart(expenses)
        except Exception as e:
            self.show_toast(f'Error: {str(e)}')

    def show_pie_chart(self, expenses):
        try:
            chart_box = self.ids.chart_box
            chart_box.clear_widgets()
            if not HAS_MATPLOTLIB:
                chart_box.add_widget(Label(
                    text='Chart unavailable in this build.',
                    color=(0.96, 0.96, 0.86, 1),
                    font_size=15,
                    size_hint_y=None,
                    height=36,
                ))
                return
            if not expenses:
                return
            paid_by = {}
            for exp in expenses:
                paid_by[exp.paid_by] = paid_by.get(exp.paid_by, 0) + exp.amount
            labels = list(paid_by.keys())
            sizes = list(paid_by.values())
            if not sizes:
                return
            fig, ax = plt.subplots(figsize=(3, 3), facecolor='#2e3640')
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140,
                   textprops={'color': 'white'})
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
            buf.seek(0)
            im = CoreImage(buf, ext='png')
            img = Image(texture=im.texture, size_hint=(None, None), size=(220, 220),
                        pos_hint={'center_x': 0.5})
            chart_box.add_widget(img)
            plt.close(fig)
        except Exception as e:
            pass  # Chart is optional; fail silently

    def settle_and_archive(self):
        try:
            participants_screen = self.manager.get_screen('participants')
            trip_name = participants_screen.ids.trip_name_input.text.strip()
            if not trip_name:
                self.show_toast('Please set a trip name before archiving!')
                return
            participants = participants_screen.participants
            expenses = self.manager.get_screen('expenses').expenses
            if not expenses:
                self.show_toast('No expenses to archive!')
                return
            balances = calculate_settlement(participants, expenses)
            file_path = save_settlement_to_excel(trip_name, participants, expenses, balances, TRIP_ARCHIVE_DIR)
            self.show_toast(f'Archived: {os.path.basename(file_path)}')
        except Exception as e:
            self.show_toast(f'Error archiving: {str(e)}')

    def show_toast(self, msg):
        layout = FloatLayout(size_hint=(None, None), size=(360, 50),
                             pos_hint={'center_x': 0.5, 'top': 0.98})
        with layout.canvas.before:
            Color(0.1, 0.1, 0.1, 0.88)
            self._toast_rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[10])
        lbl = Label(text=msg, color=(1, 1, 1, 1), bold=True, font_size=16, size_hint=(1, 1))
        layout.add_widget(lbl)
        layout.bind(pos=lambda inst, val: setattr(self._toast_rect, 'pos', val))
        layout.bind(size=lambda inst, val: setattr(self._toast_rect, 'size', val))
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self.remove_widget(layout), 2.5)

    def go_back(self):
        self.manager.current = 'participants'


class CoverScreen(Screen):
    image_path = StringProperty(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'world_silhouette.png')
    )

    def on_enter(self):
        self._elapsed = 0
        self._duration = 20  # seconds before auto-navigate
        Clock.schedule_interval(self._animate_progress, 0.05)
        Clock.schedule_once(self.goto_main, self._duration)

    def _animate_progress(self, dt):
        self._elapsed += dt
        progress = min(self._elapsed / self._duration, 1.0)
        bar = self.ids.progress_bar
        bar.size_hint_x = 0.4 * progress
        if progress >= 1.0:
            Clock.unschedule(self._animate_progress)

    def on_leave(self):
        Clock.unschedule(self._animate_progress)

    def goto_main(self, dt):
        self.manager.current = 'participants'


class ExpenseApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(CoverScreen(name='cover'))
        sm.add_widget(ParticipantsScreen(name='participants'))
        sm.add_widget(ExpensesScreen(name='expenses'))
        sm.add_widget(SettlementScreen(name='settlement'))
        sm.current = 'cover'
        return sm


if __name__ == '__main__':
    ExpenseApp().run()
