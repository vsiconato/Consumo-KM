from kivy.lang import Builder
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from database import Database
from kivy.uix.modalview import ModalView

class KmPorLitro(MDApp):
    km_last = 0  #!Para iniciar o APP zerado

    def build(self):
        self.db = Database()
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Red"

        #!Layout dp APP, esta minimizado.
        return Builder.load_string('''
BoxLayout:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)
    pos_hint: {"center_x": 0.5, "center_y": 0.5}  # Centraliza os elementos

    MDTextField:
        id: car_input
        hint_text: 'Placa do Automóvel'
        size_hint_x: 0.8  # Controla o tamanho do campo em relação à tela
        pos_hint: {"center_x": 0.5}

    MDRaisedButton:
        text: 'Adicionar veículo'
        on_release: app.add_car()
        size_hint_x: 0.5
        pos_hint: {"center_x": 0.5}

    MDLabel:
        text: 'Selecione o Veículo'
        halign: 'center'  # Centraliza o texto

    MDTextField:
        id: car_spinner
        hint_text: 'Clique para selecionar'
        on_focus: app.show_menu(self)
        size_hint_x: 0.8
        pos_hint: {"center_x": 0.5}

    MDLabel:
        text: 'Quilometragem no último abastecimento'
        halign: 'center'

    MDTextField:
        id: km_last_input
        text: str(app.km_last)
        size_hint_x: 0.8
        pos_hint: {"center_x": 0.5}

    MDLabel:
        text: 'Quilometragem atual: '
        halign: 'center'

    MDTextField:
        id: km_current_input
        size_hint_x: 0.8
        pos_hint: {"center_x": 0.5}

    MDLabel:
        text: 'Combustível abastecido (litros): '
        halign: 'center'

    MDTextField:
        id: fuel_input
        size_hint_x: 0.8
        pos_hint: {"center_x": 0.5}

    MDRaisedButton:
        text: 'Calcular e Salvar Média Km/L'
        on_release: app.calculate_and_save()
        size_hint_x: 0.7
        pos_hint: {"center_x": 0.5}

    MDLabel:
        id: result_label
        text: ''
        halign: 'center'
        size_hint_y: '0.3'

    MDRaisedButton:
        text: 'Histórico de Abastecimento'
        on_release: app.show_history()
        size_hint_x: 0.6
        pos_hint: {"center_x": 0.5}
''')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu = None

    def show_menu(self, text_field):
        car_names = self.get_car_names()
        if not car_names:
            return
        
        menu_items = [{'text': name, 'viewclass': 'OneLineListItem', 'on_release': lambda x=name: self.select_car(x)} for name in car_names]
        
        self.menu = MDDropdownMenu(
            caller=text_field,
            items=menu_items,
            position="bottom",
            width_mult=4,
        )
        self.menu.open()

    def select_car(self, car_name):
        self.root.ids.car_spinner.text = car_name
        self.menu.dismiss()
        self.update_km_last()

    def get_car_names(self):
        cars = self.db.get_cars()
        car_names = [car[1] for car in cars] if cars else []
        return car_names

    def add_car(self):
        name = self.root.ids.car_input.text.strip()
        if name:
            self.db.add_car(name)
            self.update_car_spinner()
            self.root.ids.car_input.text = ''
            self.update_km_last()

    def update_car_spinner(self):
        self.root.ids.car_spinner.text = 'Clique para selecionar'
        self.show_menu(self.root.ids.car_spinner)

    def update_km_last(self):
        selected_car_name = self.root.ids.car_spinner.text
        cars = self.db.get_cars()
        selected_car_id = [car[0] for car in cars if car[1] == selected_car_name]
        if selected_car_id:
            km_last = self.db.get_km_last(selected_car_id[0])
            self.km_last = km_last if km_last else 0
        else:
            self.km_last = 0
        self.root.ids.km_last_input.text = str(self.km_last)

    def is_number(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def calculate_and_save(self):
        try:
            selected_car_name = self.root.ids.car_spinner.text
            if not selected_car_name or selected_car_name == "Clique para selecionar":
                raise ValueError("Por favor, selecione um veículo")

            cars = self.db.get_cars()
            selected_car_id = [car[0] for car in cars if car[1] == selected_car_name][0]

            km_last = self.root.ids.km_last_input.text.strip().replace(',', '.')
            km_current = self.root.ids.km_current_input.text.strip().replace(',', '.')
            fuel = self.root.ids.fuel_input.text.strip().replace(',', '.')

            if not self.is_number(km_last) or not self.is_number(km_current) or not self.is_number(fuel):
                raise ValueError('Todos os valores devem ser números')

            km_last = float(km_last)
            km_current = float(km_current)
            fuel = float(fuel)

            if km_last >= km_current:
                raise ValueError('Ultimo KM deve ser menor que o atual')
            elif fuel <= 0:
                raise ValueError('Quantidade de combustível deve ser maior que zero')

            self.db.insert_record(selected_car_id, km_last, km_current, fuel)
            km_per_liter = (km_current - km_last) / fuel
            self.root.ids.result_label.text = f'Média: {km_per_liter:.2f} Km/L'

            self.km_last = km_current
            self.root.ids.km_last_input.text = str(self.km_last)
            self.clear_inputs()

        except ValueError as e:
            self.root.ids.result_label.text = f'Erro: {str(e)}'
        except Exception as e:
            self.root.ids.result_label.text = f'Erro Inesperado: {str(e)}'

    def clear_inputs(self):
        self.root.ids.km_current_input.text = ''
        self.root.ids.fuel_input.text = ''

    def show_history(self):
        selected_car_name = self.root.ids.car_spinner.text
        cars = self.db.get_cars()
        selected_car_id = [car[0] for car in cars if car[1] == selected_car_name]

        if selected_car_id and isinstance(selected_car_id[0], int):
            records = self.db.get_all_records(selected_car_id[0])
            history_popup = HistoryPopup(records)
            history_popup.open()
        else:
            self.root.ids.result_label.text = 'Nenhum veículo selecionado'


    def on_stop(self):
        self.db.close()

class HistoryPopup(ModalView):
    def __init__(self, records, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.7, 0.7)
        self.background_color = (1, 1, 1, 1)  # Branco sólido
        self.auto_dismiss = True

        
        layout = MDBoxLayout(orientation='vertical', spacing=10, padding=10, md_bg_color=(1, 1, 1, 1))


        # Título
        title_label = MDLabel(
            text='HISTÓRICO DE ABASTECIMENTO',
            halign='center',
            font_style='H5',
            theme_text_color='Custom',
            text_color=(0, 0, 0, 1),
            size_hint_y=0.4
        )
        layout.add_widget(title_label)

        
        records_layout = MDGridLayout(cols=4, spacing=[10, 5], size_hint_y=0.4)
        records_layout.bind(minimum_height=records_layout.setter('height'))

        
        titles = ['DATA', 'KM', 'LITROS', 'KM/L']
        for title in titles:
            title_label = MDLabel(text=title, 
                                  halign='center',
                                  font_style='Subtitle1', 
                                  theme_text_color="Custom", 
                                  text_color=(0, 0, 0, 1),
                                  size_hint_y=0.3
                                  )
            
            records_layout.add_widget(title_label)


        
        if records:
            for record in records:
                date_label = MDLabel(text=f'{record[2]}', halign='center', theme_text_color="Custom", text_color=(0, 0, 0, 1))
                km_label = MDLabel(text=f'{record[4]:.2f}', halign='center', theme_text_color="Custom", text_color=(0, 0, 0, 1))
                fuel_label = MDLabel(text=f'{record[5]:.2f}L', halign='center', theme_text_color="Custom", text_color=(0, 0, 0, 1))
                km_per_liter_label = MDLabel(text=f'{record[6]:.2f}', halign='center', theme_text_color="Custom", text_color=(0, 0, 0, 1))

                records_layout.add_widget(date_label)
                records_layout.add_widget(km_label)
                records_layout.add_widget(fuel_label)
                records_layout.add_widget(km_per_liter_label)

        else:
            records_layout.add_widget(MDLabel(text='Nenhum registro encontrado', halign='center', theme_text_color="Custom", text_color=(0, 0, 0, 1)))

        
        layout.add_widget(records_layout)

        
        self.close_button = MDFillRoundFlatButton(text='Fechar', size_hint_y=1, halign='center', text_color=(1, 1, 1, 1), md_bg_color=(1, 0, 0, 1))
        self.close_button.bind(on_release=self.dismiss)
        layout.add_widget(self.close_button)

        self.add_widget(layout)


if __name__ == '__main__':
    KmPorLitro().run()
