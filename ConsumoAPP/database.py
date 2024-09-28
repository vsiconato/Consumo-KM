import os
import sqlite3
from datetime import datetime
from kivy.utils import platform
from kivymd.app import MDApp  # Importação de MDApp, que é a classe base para aplicativos KivyMD

class Database:
    def __init__(self, db_name='fuel_date.db'):
        # Verifica se está rodando no Android
        if platform == 'android':
            # Usar o diretório de dados do aplicativo no Android
            app_storage_dir = MDApp.get_running_app().user_data_dir
            self.db_path = os.path.join(app_storage_dir, db_name)
        else:
            # Usar o diretório atual do script no desktop
            self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)

        # Conecta ao banco de dados
        self.conn = sqlite3.connect(self.db_path, isolation_level=None, timeout=10)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Cria as tabelas se elas não existirem
        with self.conn:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS cars (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS fuel_records (
                    id INTEGER PRIMARY KEY,
                    car_id INTEGER,
                    date TEXT,
                    km_last REAL,
                    km_current REAL,
                    fuel REAL,
                    km_per_liter REAL,
                    FOREIGN KEY (car_id) REFERENCES cars(id)
                )
            ''')

    def insert_record(self, car_id, km_last, km_current, fuel):
        try:
            date = datetime.now().strftime("%d-%m")
            km_per_liter = (km_current - km_last) / fuel

            with self.conn:
                self.cursor.execute(''' 
                    INSERT INTO fuel_records (car_id, date, km_last, km_current, fuel, km_per_liter)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (car_id, date, km_last, km_current, fuel, km_per_liter))
                
                # Remover registros antigos, mantendo apenas os 3 mais recentes
                self.cursor.execute('''
                    DELETE FROM fuel_records WHERE id NOT IN(
                        SELECT id FROM fuel_records ORDER BY id DESC LIMIT 2
                    )
                ''')
        except sqlite3.Error as e:
            print(f'Erro ao inserir o registro: {e}')

    def get_all_records(self, car_id):
        # Recuperar registros para o carro especificado
        self.cursor.execute('SELECT name FROM cars WHERE id = ?', (car_id,))
        if not self.cursor.fetchone():
            print(f'Veículo com ID {car_id} não encontrado.')
            return []
        
        self.cursor.execute('SELECT * FROM fuel_records WHERE car_id = ?', (car_id,))
        return self.cursor.fetchall()

    def get_km_last(self, car_id):
        # Recuperar o KM do último abastecimento
        self.cursor.execute("SELECT km_current FROM fuel_records WHERE car_id = ? ORDER BY id DESC LIMIT 1", (car_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_car(self, car_name):
        car_name = car_name.strip()
        if car_name == "" or car_name in ('Selecione o Veículo', 's'):
            print(f'Nome inválido: {car_name}')
            return
        
        self.cursor.execute('SELECT name FROM cars WHERE name = ?', (car_name,))
        if self.cursor.fetchone():
            print(f'Veículo {car_name} já existe no banco de dados.')
            return
        
        try:
            with self.conn:
                self.cursor.execute('INSERT INTO cars (name) VALUES (?)', (car_name,))
                print(f'Veículo {car_name} adicionado com sucesso.')
        except sqlite3.Error as e:
            print(f'Erro ao adicionar o automóvel: {e}')

    def get_cars(self):
        # Recuperar todos os carros
        query = "SELECT * FROM cars"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def delete_car(self, car_id):
        try:
            with self.conn:
                # Remover registros de abastecimento associados ao carro
                self.cursor.execute('DELETE FROM fuel_records WHERE car_id = ?', (car_id,))
                # Remover o carro
                self.cursor.execute('DELETE FROM cars WHERE id = ?', (car_id,))
                print(f'Veículo com ID {car_id} removido com sucesso.')
        except sqlite3.Error as e:
            print(f'Erro ao remover o veículo: {e}')

    def close(self):
        self.cursor.close()
        self.conn.close()

    def clean_invalid_cars(self):
        # Remover veículos com nomes inválidos
        query = "DELETE FROM cars WHERE name IN ('Meu Carro', 'Selecione o Veículo', 's')"
        with self.conn:
            self.cursor.execute(query)
        print('Registros inválidos removidos')

if __name__ == '__main__':
    db = Database()
    db.insert_record(1, 10000, 10500, 50)
    records = db.get_all_records(1)
    db.clean_invalid_cars()
    db.close()
