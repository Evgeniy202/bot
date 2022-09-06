from cgitb import text
from operator import le
from webbrowser import get
from telebot import types
import telebot
import sqlite3
import re

import config


adminId = config.MAIN_ADMIN_ID
bot = telebot.TeleBot(config.TOKEN)

def adminAudit(message):
    usName = message.from_user.username
    val = ''
    status = ''

    conn = sqlite3.connect('root.sqlite3')
    cur = conn.cursor()

    cur.execute(f"SELECT name FROM admins WHERE name IN ('{usName}')")

    for val in cur:
        status = val

    res = [status, conn, cur]
    return res

@bot.message_handler(commands = ["start"])
def start(message):
    username = message.from_user.username
    userId = message.from_user.id
    statusReq = ''
    statusUsser = ''
    val = ''

    conn = sqlite3.connect('root.sqlite3')
    cur = conn.cursor()

    if str(message.from_user.id) == str(adminId):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttonAdm = types.KeyboardButton('/AdminPanel')
        markup.add(buttonAdm)
        bot.send_message(
            message.chat.id,
            'Для переходу в адміністрування: /AdminPanel',
            reply_markup = markup
        )
    else:
        cur.execute(f"SELECT id, active FROM users WHERE id IN ('{userId}')")
        for val, active in cur:
            statusUsser = val

        if statusUsser != '':
            if active == 0:
                cur.execute(f"UPDATE users SET active = 1 WHERE id = {statusUsser}")
            bot.send_message(
                message.chat.id, 
                f"Підписка на новини активована!\n" 
                "Якщо ви бажаєте відмовитись від підписки введіть команду'/unsubscribe'"
            )

        else:
            cur.execute(f"SELECT id FROM requests WHERE id IN ('{userId}')")

            for val in cur:
                statusReq = val

            if statusReq != '':
                bot.send_message(message.chat.id, "Будь-ласка почекайте, ваша заявка в обробці.")
            else:
                cur.execute(f"INSERT INTO requests VALUES ('{userId}', '{username}')")
                bot.send_message(message.chat.id, f"Заявка на підписку подано, будь-ласка почекайте.")

    conn.commit()
    conn.close()

@bot.message_handler(commands = ['AdminPanel'])
def adminPanelActivite(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/Add_News', '/RequestsMenu', '/Manage_Admins', '/Manage_Users']

        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        bot.send_message(message.chat.id, "Адміністрування", reply_markup=rmk)
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands=['Manage_Users'])
def manageUsers(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/List_all_users', '/List_not_active_users', '/Statistics_active', '/Remove_user', '/AdminPanel']
        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        bot.send_message(message.chat.id, "Управління користувачами...", reply_markup=rmk)
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands=['Remove_user'])
def userControl(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        rmk.add(types.KeyboardButton("/Manage_Users"))

        bot.send_message(
            message.chat.id, 
            "Для видалення користувача потрібно заповнити дані наступним чином:\n"
            '"/deleteuser name ЛОГІН_КОРИСТУВАЧА" або "/deleteuser id ID_КОРИСТУВАЧА"',
            reply_markup=rmk
        )
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands=['List_all_users', 'List_not_active_users', 'Statistics_active'])
def listUsers(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    cur = getList[2]

    if status != '':
        if message.text == "/List_all_users":
            i = 0
            cur.execute("SELECT * FROM users")

            bot.send_message(message.chat.id, "<=====Користувачі=====>")
            for userId, name, active in cur:
                if active == 1:
                    active = "Активний"
                elif active == 0:
                    active = "Не активний"
                if name != None:
                    bot.send_message(message.chat.id, f"ID: {userId}, Логін: @{name}, Активнысть: {active}")
                else:
                    name = "Не вказаний"
                    bot.send_message(message.chat.id, f"ID: {userId}, Логін: {name}, Активнысть: {active}")
                i+=1
            bot.send_message(message.chat.id, f"<=====Всього {i}=====>")
        elif message.text == "/List_not_active_users":
            i = 0
            cur.execute("SELECT * FROM users WHERE active = 0")

            bot.send_message(message.chat.id, "<=Не активні коистувічі=>")
            for userId, name, active in cur:
                bot.send_message(message.chat.id, f"ID: {userId}, Логін: {name}, Активнысть: {active}")
                i+=1
            bot.send_message(message.chat.id, f"<======Всього {i}======>")
        elif message.text == "/Statistics_active":
            allUsers = []
            notActiveUsers = []
            cur.execute("SELECT * FROM users")
            for val in cur:
                allUsers.append(val)
            cur.execute("SELECT * FROM users WHERE active = 1")
            for val in cur:
                notActiveUsers.append(val)
            try:
                res = (len(notActiveUsers) / len(allUsers)) * 100
                bot.send_message(message.chat.id, f"Відсоток активних коростивочів: {res}%")
            except:
                bot.send_message(message.chat.id, "Підписок немає...")

        manageUsers(message)
        
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands=['RequestsMenu'])
def requests(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/Lists', '/Request', '/AdminPanel']

        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        bot.send_message(message.chat.id, "Запити на підписку:", reply_markup = rmk)
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands = ['Lists'])
def reqList(message):
    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    cur = getList[2]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/Lists', '/Request', '/RequestsMenu']

        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        cur.execute("SELECT * FROM requests")
        bot.send_message(message.chat.id, "<===================>")
        if cur != '':
            for id, name in cur:
                if name == 'None':
                    name = "Ім'я користувача невідоме"
                bot.send_message(message.chat.id, f"Id: {id}, Name: @{name}")
            bot.send_message(message.chat.id, 'Натисніть "Request" для розгляду заявок',reply_markup = rmk)
        else:
            bot.send_message(message.chat.id, "Запитів немає.")
        bot.send_message(message.chat.id, "<===================>")
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands = ['Request'])
def requestsManage(message):
    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    cur = getList[2]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/Request', '/Yes', '/No', '/RequestsMenu']
        id = ''

        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        cur.execute("SELECT * FROM requests")
        for id, name in cur:
            bot.send_message(message.chat.id, f"Id: {id}, Ім'я: @{name}", reply_markup = rmk)
            break
        if id == '':
            bot.send_message(message.chat.id, "Наразі запитиів немає.")
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands = ['Yes', 'No'])
def choiceReq(message):
    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    cur = getList[2]

    if status != '':

        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/Lists', '/Request', '/RequestsMenu']

        for btn in btns:
           rmk.add(types.KeyboardButton(btn))

        if message.text == '/Yes':
            cur.execute("SELECT * FROM requests")
            for id, name in cur:
                cur.execute(f"INSERT INTO users VALUES ('{id}', '{name}', 1)")
                cur.execute(f"DELETE FROM requests WHERE ID = {id}")
                if name == None:
                    bot.send_message(
                        message.chat.id, 
                        f"Запит на підписку користувача: ID: {id} підтверджений!",
                        reply_markup=rmk
                    )
                else:
                    bot.send_message(
                        message.chat.id, 
                        f"Запит на підписку користувача: @{name} підтверджений!",
                        reply_markup = rmk
                    )
                try: 
                    bot.send_message(id, "Ваш запит підтвержено!")
                    break
                except:
                    break
        elif message.text == '/No':
            cur.execute("SELECT * FROM requests")
            for id, name in cur:
                cur.execute(f"DELETE FROM requests WHERE ID = {id}")
                if name == None:
                    name == id
                bot.send_message(
                    message.chat.id, 
                    f"Запит на підписку користувача: @{name} скасовано!",
                    reply_markup = rmk
                )
                try:
                    bot.send_message(id, "Ваш запит скасовано!")
                    break
                except:
                    break
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.") 

    conn.commit()
    conn.close()

@bot.message_handler(commands=["Add_News"])
def addNews(message):
    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ('/send', '/cancel', '/AdminPanel')
        for btn in btns:
            rmk.row(types.KeyboardButton(btn))

        bot.send_message(
            message.chat.id,
            "Напишіть новину, після чого натисніть , для скасування даної дії натисніть '/cancel'" ,
            reply_markup=rmk     
        )                        
    else:                        
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")
                                 
    conn.close()                 
                                 
@bot.message_handler(commands=['send'])
def messAction(message):         
    getList = adminAudit(message)
    status = getList[0]          
    conn = getList[1]            
    cur = getList[2]             
                                 
    if status != '':            
        offUser = []
        remUSer = []

        cur.execute("SELECT * FROM users WHERE active = 1")

        for idUser, name, active in cur:   
            try:  
                bot.forward_message(idUser, message.chat.id, message.message_id - 1)
            except Exception as error:
                if re.search(r'Description:\s(.*)', str(error)).group(1) == "Forbidden: bot was blocked by the user":
                    offUser.append(idUser)
                elif re.search(r'Description:\s(.*)', str(error)).group(1) == "Bad Request: chat not found":
                    remUSer.append(idUser)

        if len(offUser) != 0:
            for idUser in offUser:
                cur.execute(f"UPDATE users SET active = 0 WHERE id = {idUser}")
        if len(remUSer) != 0:
            for idUser in remUSer:
                cur.execute(f"DELETE FROM users WHERE id = {idUser}")
        
        bot.send_message(message.chat.id, "Новина переслана!")
        adminPanelActivite(message)

    else:                        
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.commit()               
    conn.close()

@bot.message_handler(commands=['Manage_Admins'])
def managerAdmin(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    
    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/list_Admins', '/add_Admin', '/remove_Admin', '/AdminPanel']
        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        bot.send_message(message.chat.id, "Управління адміністраторами:", reply_markup=rmk)  
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands=['list_Admins'])
def listAdmins(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    cur = getList[2]

    if status != '':
        cur.execute("SELECT * FROM admins")
        bot.send_message(message.chat.id, "<===================>")
        for name in cur:
            bot.send_message(message.chat.id, f"Name: @{name[0]}")
        bot.send_message(message.chat.id, "<===================>")
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()

@bot.message_handler(commands=['add_Admin'])    
def addAdmin(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/Cancel']
        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        bot.send_message(
            message.chat.id, 
            "Будьласка введіть ім'я нового адміністратора (в форматі: '/Add @Username' або '/Add Username')...", 
            reply_markup=rmk
        )
        
    conn.commit()                
    conn.close() 
           
@bot.message_handler(commands=['Add'])
def addNewAdm(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    cur = getList[2]
     
    if status != '':  
        admName = message.text.replace(' ', '')     
        admName = admName[4:]
        if admName[0] == '@':
            cur.execute(f"INSERT INTO admins VALUES ('{admName[1:]}')")
            bot.send_message(message.chat.id, f"Вітаємо! {admName} тепер адмістратор!")
        else:
            cur.execute(f"INSERT INTO admins VALUES ('{admName}')")
            bot.send_message(message.chat.id, f"Вітаємо! @{admName} тепер адмістратор!")
        managerAdmin(message)
    
    else:           
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")
        
    conn.commit()                
    conn.close()    
                    
@bot.message_handler(commands=['remove_Admin'])
def removeAdmin(message):
                    
    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status != '':
        rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btns = ['/Cancel']
        for btn in btns:
            rmk.add(types.KeyboardButton(btn))

        bot.send_message(
            message.chat.id, 
            "Будьласка введіть ім'я адміністратора (в форматі: '/Remove @Username' або '/Remove Username')...", 
            reply_markup=rmk
        ) 
    else:
        bot.send_message(message.chat.id, "Помилка! У вас немає доступу.")

    conn.close()  

@bot.message_handler(commands=['Remove'])
def removeAdm(message):

    getList = adminAudit(message)
    conn = getList[1]
    cur = getList[2]
    
    admName = message.text.replace(' ', '')
    admName = admName[7:]
    
    if admName[0] == '@':
        cur.execute(f"DELETE FROM admins WHERE name = ('{admName[1:]}')")
        bot.send_message(message.chat.id, f"{admName} видалено статус адмістратора!")
    else:
        cur.execute(f"DELETE FROM admins WHERE name = ('{admName}')")
        bot.send_message(message.chat.id, f"@{admName} видалено статус адмістратора!")
    managerAdmin(message)

    conn.commit()
    conn.close()    

@bot.message_handler(commands=['Cancel'])
def cancelActionAdmin(message):
    
    managerAdmin(message)

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):

    getList = adminAudit(message)
    conn = getList[1]
    cur = getList[2]

    cur.execute(f"DELETE FROM users WHERE ID = {message.from_user.id}")

    bot.send_message(message.chat.id, "Ваша підписка скасована!")

    conn.commit()
    conn.close()
    
@bot.message_handler(commands=['deleteuser'])
def deleteUser(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]
    cur = getList[2]

    if status != '':
        string = message.text.replace(' ', '')
        string = string[11:]

        if (
            (string[0] == "n") and
            (string[1] == 'a') and
            (string[2] == 'm') and
            (string[3] == 'e')
        ):
            string = string[4:]
            if string[0] == "@":
                string = string[1:]
            try:
                cur.execute(f"DELETE FROM users WHERE name = ('{string}')")
                bot.send_message(message.chat.id, f"Користувач з логіном {string} видалений!")
            except:
                bot.send_message(
                    message.chat.id, 
                    f"Помилка!"
                )
        elif (string[0] == "i") and (string[1] == "d"):
            string = string[2:]
            try:
                cur.execute(f"DELETE FROM users WHERE id = ('{string}')")
                bot.send_message(message.chat.id, f"Користувач з ID {string} видалений!")
            except:
                bot.send_message(
                    message.chat.id, 
                    f"Користувач з id {string} не знайдений, перевірте правельність написання лолгіну!"
                )
                          
    conn.commit()
    conn.close()
    
    manageUsers(message)
    
@bot.message_handler(commands=['cancel'])
def cancelAddNews(message):
    
    addNews(message)

@bot.message_handler(content_types=['text'])
def otherText(message):

    getList = adminAudit(message)
    status = getList[0]
    conn = getList[1]

    if status == '':
        bot.delete_message(message.chat.id, message.message_id)

    conn.close()


bot.polling(none_stop=True)


