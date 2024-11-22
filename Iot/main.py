import network
import time
import json

from umqtt.simple import MQTTClient
from machine import ADC, Pin

SSID = "Wokwi-GUEST"
PASSWORD = "" 

BROKER_MQTT = "broker.hivemq.com"
PORT = 1883
CLIENT_ID = "esp32_mqtt_led"
TOPIC_PUBLISH_LEDS = "fiap/iot/leds"

led1 = Pin(15, Pin.OUT)
led2 = Pin(16, Pin.OUT)
led3 = Pin(17, Pin.OUT)
led4 = Pin(18, Pin.OUT)

potenciometro_geladeira = ADC(Pin(25))
potenciometro_tv = ADC(Pin(26))
potenciometro_ar = ADC(Pin(33))
potenciometro_chuveiro = ADC(Pin(32))

for potenciometro in [potenciometro_geladeira, potenciometro_tv, potenciometro_ar, potenciometro_chuveiro]:
    potenciometro.width(ADC.WIDTH_12BIT)
    potenciometro.atten(ADC.ATTN_11DB)

PRECO_KWH = 0.656

POWER_PER_LED = 0.06
LAMPADA_MULTIPLICADOR = 60 / POWER_PER_LED

def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(SSID, PASSWORD)
    
    while not wifi.isconnected():
        print("Conectando ao WiFi...")
        time.sleep(1)
    
    print("Conectado ao WiFi. IP:", wifi.ifconfig()[0])

def connect_mqtt():
    client = MQTTClient(CLIENT_ID, BROKER_MQTT, PORT)
    client.connect()
    print("Conectado ao broker MQTT!")
    return client

def ler_potencia(potenciometro, potenciometro_nome, potencia_maxima):
    try:
        valor_analogico = potenciometro.read()
        potencia = (valor_analogico / 4095) * potencia_maxima
        print(f"Dispositivo: {potenciometro_nome}")
        print(f"  Valor Analógico: {valor_analogico}")
        print(f"  Potência: {potencia:.2f} W")
        print("-" * 30)
        return potencia
    except Exception as e:
        print(f"Erro ao ler {potenciometro_nome}: {e}")
        return 0

def calcular_consumo_diario():
    consumo_geladeira = ler_potencia(potenciometro_geladeira, "Geladeira", 150)
    consumo_tv = ler_potencia(potenciometro_tv, "Televisão", 100)
    consumo_ar = ler_potencia(potenciometro_ar, "Ar Condicionado", 1500)
    consumo_chuveiro = ler_potencia(potenciometro_chuveiro, "Chuveiro", 5000)

    print("\nDigite as horas de uso de cada aparelho:")
    horas_geladeira = float(input("Geladeira (horas): "))
    horas_tv = float(input("Televisão (horas): "))
    horas_ar = float(input("Ar Condicionado (horas): "))
    horas_chuveiro = float(input("Chuveiro (horas): "))

    consumo_kwh_geladeira = (consumo_geladeira * horas_geladeira) / 1000
    consumo_kwh_tv = (consumo_tv * horas_tv) / 1000
    consumo_kwh_ar = (consumo_ar * horas_ar) / 1000
    consumo_kwh_chuveiro = (consumo_chuveiro * horas_chuveiro) / 1000

    custo_geladeira = consumo_kwh_geladeira * PRECO_KWH
    custo_tv = consumo_kwh_tv * PRECO_KWH
    custo_ar = consumo_kwh_ar * PRECO_KWH
    custo_chuveiro = consumo_kwh_chuveiro * PRECO_KWH

    print("\n--- RELATÓRIO DE CONSUMO ---")
    print(f"Geladeira: Consumo: {consumo_kwh_geladeira:.2f} kWh, Custo: R$ {custo_geladeira:.2f}")
    print(f"Televisão: Consumo: {consumo_kwh_tv:.2f} kWh, Custo: R$ {custo_tv:.2f}")
    print(f"Ar Condicionado: Consumo: {consumo_kwh_ar:.2f} kWh, Custo: R$ {custo_ar:.2f}")
    print(f"Chuveiro: Consumo: {consumo_kwh_chuveiro:.2f} kWh, Custo: R$ {custo_chuveiro:.2f}")

    consumo_total_kwh = consumo_kwh_geladeira + consumo_kwh_tv + consumo_kwh_ar + consumo_kwh_chuveiro
    custo_total = consumo_total_kwh * PRECO_KWH

    print("\n--- CONSUMO TOTAL ---")
    print(f"Consumo Total: {consumo_total_kwh:.2f} kWh, Custo Total: R$ {custo_total:.2f}")

def calcular_previsao_consumo():
    consumo_geladeira = ler_potencia(potenciometro_geladeira, "Geladeira", 150)
    consumo_tv = ler_potencia(potenciometro_tv, "Televisão", 100)
    consumo_ar = ler_potencia(potenciometro_ar, "Ar Condicionado", 1500)
    consumo_chuveiro = ler_potencia(potenciometro_chuveiro, "Chuveiro", 5000)

    print("\nDigite as horas médias de uso diário de cada aparelho:")
    horas_geladeira = float(input("Geladeira (horas/dia): "))
    horas_tv = float(input("Televisão (horas/dia): "))
    horas_ar = float(input("Ar Condicionado (horas/dia): "))
    horas_chuveiro = float(input("Chuveiro (horas/dia): "))

    periodos = {'1 Mês': 30, '3 Meses': 90, '6 Meses': 180, '1 Ano': 365}

    def calcular_consumo_aparelho(consumo_watts, horas_uso):
        consumo_diario_kwh = (consumo_watts * horas_uso) / 1000
        previsoes = {}
        for periodo, dias in periodos.items():
            consumo_kwh = consumo_diario_kwh * dias
            custo = consumo_kwh * PRECO_KWH
            previsoes[periodo] = {'consumo_kwh': consumo_kwh, 'custo_rs': custo}
        return previsoes

    previsoes_geladeira = calcular_consumo_aparelho(consumo_geladeira, horas_geladeira)
    previsoes_tv = calcular_consumo_aparelho(consumo_tv, horas_tv)
    previsoes_ar = calcular_consumo_aparelho(consumo_ar, horas_ar)
    previsoes_chuveiro = calcular_consumo_aparelho(consumo_chuveiro, horas_chuveiro)

    def imprimir_previsoes(nome_aparelho, previsoes):
        print(f"\n--- Previsão de Consumo - {nome_aparelho} ---")
        for periodo, dados in previsoes.items():
            print(f"{periodo}: Consumo: {dados['consumo_kwh']:.2f} kWh, Custo: R$ {dados['custo_rs']:.2f}")

    imprimir_previsoes("Geladeira", previsoes_geladeira)
    imprimir_previsoes("Televisão", previsoes_tv)
    imprimir_previsoes("Ar Condicionado", previsoes_ar)
    imprimir_previsoes("Chuveiro", previsoes_chuveiro)

    def calcular_total_previsoes(previsoes_aparelhos):
        totais = {}
        for periodo in periodos.keys():
            consumo_total_kwh = sum(previsoes[periodo]['consumo_kwh'] for previsoes in previsoes_aparelhos)
            custo_total = consumo_total_kwh * PRECO_KWH
            totais[periodo] = {'consumo_kwh': consumo_total_kwh, 'custo_rs': custo_total}
        return totais

    totais_previsao = calcular_total_previsoes([previsoes_geladeira, previsoes_tv, previsoes_ar, previsoes_chuveiro])

    print("\n--- PREVISÃO DE CONSUMO TOTAL ---")
    for periodo, dados in totais_previsao.items():
        print(f"{periodo}: Consumo Total: {dados['consumo_kwh']:.2f} kWh, Custo Total: R$ {dados['custo_rs']:.2f}")


def visualizar_atividade_leds(client):
    leds_states = {
        "LED1": led1.value(), 
        "LED2": led2.value(), 
        "LED3": led3.value(), 
        "LED4": led4.value()
    }
    qtd_leds_acesos = sum(leds_states.values())
    consumo_simulado = qtd_leds_acesos * POWER_PER_LED * LAMPADA_MULTIPLICADOR

    print("\n--- ESTADO DOS LEDS E CONSUMO (SIMULADO COMO LÂMPADAS) ---")
    for led, estado in leds_states.items():
        estado_str = "Ligado" if estado else "Desligado"
        print(f"{led}: {estado_str}")

    print(f"Quantidade de LEDs Acesos: {qtd_leds_acesos}")
    print(f"Consumo Total Simulado: {consumo_simulado:.2f} W")

    horas_uso = float(input("\nDigite as horas de uso no estado atual: "))
    consumo_kwh = (consumo_simulado * horas_uso) / 1000
    custo_total = consumo_kwh * PRECO_KWH
    print(f"Custo estimado para {horas_uso} horas de uso: R$ {custo_total:.2f}")

    payload = {
        "LED1": bool(leds_states["LED1"]),
        "LED2": bool(leds_states["LED2"]),
        "LED3": bool(leds_states["LED3"]),
        "LED4": bool(leds_states["LED4"]),
        "Consumo": round(consumo_simulado, 2)
    }
    
    try:
        payload_json = json.dumps(payload)
        client.publish(TOPIC_PUBLISH_LEDS, payload_json)
        print("Estado dos LEDs publicado via MQTT:", payload_json)
    except Exception as e:
        print(f"Erro ao serializar JSON: {e}")

def menu_principal(client):
    while True:
        print("\n--- MENU DE MONITORAMENTO ENERGÉTICO ---")
        print("1 - Medição diária de consumo dos aparelhos")
        print("2 - Previsão de consumo e gastos")
        print("3 - Visualizar atividade dos LEDs")
        print("0 - Sair")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == '1':
            calcular_consumo_diario()
        elif opcao == '2':
            calcular_previsao_consumo()
        elif opcao == '3':
            visualizar_atividade_leds(client)
        elif opcao == '0':
            print("Encerrando o programa...")
            break
        else:
            print("Opção inválida. Tente novamente.")

connect_wifi()
client = connect_mqtt()
menu_principal(client)