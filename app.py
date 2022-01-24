from flask import Flask, request, render_template, redirect
import datetime
import string
import random
import json 

app = Flask(__name__)
initial_time = 0
def abb_gen():
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(5)))
    return result_str

def read_data():
    with open('data.json', 'r') as f:
        data = json.load(f)
    return data

def write_data(new_data):
    with open('data.json', 'w+') as f:
        json.dump(new_data, f)
    return

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method=="POST":
        abbr = abb_gen()
        data = read_data()
        password = random.randint(1000, 9999)
        data[abbr] = {"currentToken":0, "tokens":{},"initialTime":0 ,"estTime":0, "password":password}
        write_data(data)
        return render_template("urldisplay.html", user_url=f"https://tokensys.herokuapp.com/{abbr}", admin_url=f"https://tokensys.herokuapp.com/{abbr}/admin?password={password}")
    return render_template("index.html")

@app.route("/<string:abbr>/", methods=["GET", "POST"])
def gen_token(abbr):
    data = read_data()
    check = data.get(abbr, 0)
    if check==0:
        return "This form has been deleted by admin!"
    if request.method=="POST":
        tk_abbr = abb_gen()
        token_number = len(data[abbr]["tokens"])+1
        data[abbr]["tokens"][tk_abbr] = token_number
        write_data(data)
        return redirect(f"/{abbr}/user?tkid={tk_abbr}")
    else:
        return render_template("gettokens.html", total_tokens=len(data[abbr]["tokens"]), abbr=abbr)

@app.route("/<string:abbr>/gettoken", methods=["GET", "POST"])
def gen_token_qr(abbr):
    data = read_data()
    check = data.get(abbr, 0)
    if check==0:
        return "This form has been deleted by admin!"
    tk_abbr = abb_gen()
    token_number = len(data[abbr]["tokens"])+1
    data[abbr]["tokens"][tk_abbr] = token_number
    write_data(data)
    return redirect(f"/{abbr}/user?tkid={tk_abbr}")


@app.route("/<string:abbr>/user", methods=["GET", "POST"])
def user(abbr):
    current_date = datetime.datetime.now()
    data = read_data()
    check = data.get(abbr, 0)
    if check==0:
        return "This form has been deleted by admin!"
    tk_abbr = request.args.get("tkid")
    my_token = data[abbr]["tokens"][tk_abbr]
    current_token = data[abbr]["currentToken"]
    msg = ""
    sound = "muted"
    estTime = ((int(data[abbr]["estTime"])-data[abbr]["initialTime"])/60)*(current_token-my_token)
    if estTime<=0:
        estTime*=-1
    if current_token==0:
        estTime = 0
    if my_token==current_token:
        msg = "You're up!"
        sound = ""
    elif current_token>my_token:
        return "Your Token has expired. Thank you for using the service!"
    return render_template("user.html", current_token=current_token, my_token=my_token, estTime=format(estTime, ".2f"), message=msg, sound=sound)

@app.route("/<string:abbr>/admin", methods=["GET", "POST"])
def admin(abbr):
    current_date = datetime.datetime.now()
    data = read_data()
    password = request.args.get("password")
    if int(data[abbr]["password"])!=int(password):
        return "Password is incorrect, Kindly check the URL again!"
    if request.method=="POST":
        if request.form['submit_button'] == 'next':
            if data[abbr]["currentToken"]!=len(data[abbr]["tokens"]):
                data[abbr]["currentToken"]=data[abbr]["currentToken"]+1
                if data[abbr]["currentToken"]==1:
                    data[abbr]["initialTime"] = int(current_date.strftime("%H%M%S"))
                    data[abbr]["estTime"] = data[abbr]["initialTime"]
                elif data[abbr]["currentToken"]==2:
                    data[abbr]["estTime"] = int((int(current_date.strftime("%H%M%S"))+data[abbr]["initialTime"])/2)
                else:
                    print("before token3", data[abbr]["estTime"])
                    data[abbr]["estTime"] = int((int(current_date.strftime("%H%M%S"))+(int((data[abbr]["estTime"]))))/2)
        elif request.form['submit_button'] == 'previous':
            if data[abbr]["currentToken"]>0:
                data[abbr]["currentToken"]=data[abbr]["currentToken"]-1
        elif request.form['submit_button'] == 'close':
            data.pop(abbr)
            write_data(data)
            return "Form Destroyed!"
        write_data(data)
    estTime=0
    if data[abbr]["estTime"]!=0:
        estTime = ((int(current_date.strftime("%H%M%S"))-int(data[abbr]["estTime"]))/60)
    total_tokens = len(data[abbr]["tokens"])
    return render_template("admin.html", current_token=data[abbr]["currentToken"], estTime = format(estTime, ".2f"), total_tokens=total_tokens)
    

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
