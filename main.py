from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from database import Database
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

class KmPorLitro(App):
    def build(self):
        self.db = Database()
        self.layout = BoxLayout(orientation='vertical')

        self.car_spinner = Spinner(text='Selecione o Veículo', values=self.get_car_names())
        self.car_spinner.bind(text=self.on_car_selected)  # Vincule o método de seleção
        self.layout.add_widget(self.car_spinner)

        self.car_input = TextInput(hint_text='Placa do Automóvel')
        self.layout.add_widget(self.car_input)

        self.add_car_button = Button(text='Adicionar veículo')
        self.add_car_button.bind(on_press=self.add_car)
        self.layout.add_widget(self.add_car_button)

        # Carregar o Km do último abastecimento
        self.km_last = 0

        # Configuração da Interface
        self.setup_main_interface()

        # Atualizar KM do último abastecimento ao iniciar
        self.update_km_last()

        return self.layout

    def setup_main_interface(self):
        # Último Abastecimento
        self.km_last_label = Label(text='Quilometragem no último abastecimento')
        self.layout.add_widget(self.km_last_label)
        self.km_last_input = TextInput(text=str(self.km_last))
        self.layout.add_widget(self.km_last_input)

        # KM Atual
        self.km_current_label = Label(text='Quilometragem atual: ')
        self.layout.add_widget(self.km_current_label)
        self.km_current_input = TextInput()
        self.layout.add_widget(self.km_current_input)

        # Quanto abasteceu
        self.fuel_label = Label(text='Combustível abastecido (litros): ')
        self.layout.add_widget(self.fuel_label)
        self.fuel_input = TextInput()
        self.layout.add_widget(self.fuel_input)

        # Botão para calcular e salvar
        self.calculate_button = Button(text='Calcular e Salvar Média Km/L')
        self.calculate_button.bind(on_press=self.calculate_and_save)
        self.layout.add_widget(self.calculate_button)

        self.result_label = Label(text='')
        self.layout.add_widget(self.result_label)

        # Mostra o histórico de abastecimento
        self.view_history_button = Button(text='Histórico de Abastecimento')
        self.view_history_button.bind(on_press=self.show_history)
        self.layout.add_widget(self.view_history_button)

    def on_car_selected(self, spinner, text):
        self.update_km_last()

    def add_car(self, instance):
        name = self.car_input.text.strip()
        if name:
            self.db.add_car(name)
            self.car_spinner.values = self.get_car_names()
            self.car_input.text = ''
            # Atualiza a KM do último abastecimento ao adicionar um carro
            self.update_km_last()

    def get_car_names(self):
        cars = self.db.get_cars()
        car_names = [car[1] for car in cars] if cars else []
        print(f'Veículos no banco de dados: {car_names}')
        return car_names

    def update_km_last(self):
        selected_car_name = self.car_spinner.text
        cars = self.db.get_cars()
        selected_car_id = [car[0] for car in cars if car[1] == selected_car_name]
        if selected_car_id:
            km_last = self.db.get_km_last(selected_car_id[0])
            self.km_last = km_last if km_last else 0
        else:
            self.km_last = 0
        self.km_last_input.text = str(self.km_last)

    def is_number(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def calculate_and_save(self, instance):
        try:
            selected_car_name = self.car_spinner.text
            if not selected_car_name or selected_car_name == "Selecione o Veículo":
                raise ValueError("Por favor, selecione um veículo")

            cars = self.db.get_cars()
            selected_car_id = [car[0] for car in cars if car[1] == selected_car_name][0]

            km_last = self.km_last_input.text.strip().replace(',', '.')
            km_current = self.km_current_input.text.strip().replace(',', '.')
            fuel = self.fuel_input.text.strip().replace(',', '.')

            if not self.is_number(km_last) or not self.is_number(km_current) or not self.is_number(fuel):
                raise ValueError('Todos os valores devem ser números')

            km_last = float(km_last)
            km_current = float(km_current)
            fuel = float(fuel)

            if km_last >= km_current:
                raise ValueError('km_last deve ser menor que km_current')
            elif fuel <= 0:
                raise ValueError('Quantidade de combustível deve ser maior que zero')

            self.db.insert_record(selected_car_id, km_last, km_current, fuel)
            km_per_liter = (km_current - km_last) / fuel
            self.result_label.text = f'Média: {km_per_liter:.2f} Km/L'

            self.km_last = km_current
            self.km_last_input.text = str(self.km_last)
            self.clear_inputs()

        except ValueError as e:
            self.result_label.text = f'Erro: {str(e)}'
        except Exception as e:
            self.result_label.text = f'Erro Inesperado: {str(e)}'

    def clear_inputs(self):
        self.km_current_input.text = ''
        self.fuel_input.text = ''

    def show_history(self, instance):
        selected_car_name = self.car_spinner.text
        cars = self.db.get_cars()
        selected_car_id = [car[0] for car in cars if car[1] == selected_car_name]

        if selected_car_id and isinstance(selected_car_id[0], int):
            records = self.db.get_all_records(selected_car_id[0])
            history_popup = HistoryPopup(records)
            history_popup.open()
        else:
            self.result_label.text = 'Nenhum veículo selecionado'

    def on_stop(self):
        self.db.close()

class HistoryPopup(Popup):
    def __init__(self, records, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Histórico de Abastecimento'
        self.size_hint = (0.9, 0.9)
        self.layout = BoxLayout(orientation='vertical')

        if records:
            for record in records:
                record_label = Label(text=f'Data: {record[2]}\n'
                                    f'Km do Abastecimento: {record[4]:.2f}\n'
                                    f'Litros abastecido: {record[5]:.2f}L\n'
                                    f'Km/L: {record[6]:.2f}'
                                    )
                self.layout.add_widget(record_label)
        else:
            self.layout.add_widget(Label(text='Nenhum registro encontrado'))

        self.close_button = Button(text='Fechar', size_hint_y=None, height=100)
        self.close_button.bind(on_press=self.dismiss)
        self.layout.add_widget(self.close_button)

        self.add_widget(self.layout)

if __name__ == '__main__':
    KmPorLitro().run()
