# Beeline Personal Assistant
Этот Telegram-бот является неофициальным помощником личного кабинета Билайн. Он позволяет вам удобно и быстро получать всю необходимую информацию о вашем аккаунте в Билайн, в том числе:
- Проверить баланс и остаток пакетов минут, СМС и интернета
- Просмотреть детализацию по использованию интернета
- Узнать текущий тариф и услуги (в том числе скрытые)
- Проверить наличие подписок и "вредных" услуг

## Как работает
1. Для начала необходимо найти бота в Telegram 
2. Нажмите на кнопку "Начать"
3. Отправьте боту ваш номер телефона и пароль в формате +7XXXXXXXXXX пароль
4. В течение нескольких секунд вы получите доступ к своему личному кабинету


## Установка

    git clone https://github.com/phys-winner/beeline-personal-assistant-bot
    cd beeline-personal-assistant-bot
    git checkout
    py -m venv env
    .\env\Scripts\pip install -r requirements.txt

## Запуск
Перед первым запуском создайте файл **src\config_secrets.py** ([**пример**](src/config_secrets.example.py)) и укажите в нём токен для бота Telegram.

    cd beeline-personal-assistant-bot
    .\env\Scripts\python src\main.py


## Использованные технологии

- [**beeline-usss-mock**](https://github.com/arthurvaverko-kaltura/beeline-usss-mock) - описание API билайна;
- [**официальное приложение билайна 4.0.4**](https://4pda.to/forum/index.php?s=&showtopic=258284&view=findpost&p=79490601) - API для подключения услуг;
- **Python 3.9**
- **python-telegram-bot**
- **ratelimiter**
- **requests**



Этот бот распространяется под лицензией MIT. Это означает, что вы можете свободно использовать, копировать и модифицировать код, соблюдая условия лицензии. Подробнее о лицензии можно узнать в файле LICENSE, входящем в состав репозитория.