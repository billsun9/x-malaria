from flask import Flask, request, render_template
from datetime import date
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user_info', methods=['GET', 'POST'])
def user_info():
    return render_template('info.html')

@app.route('/continue', methods=['GET', 'POST'])
def save_info():
    country = request.form['country']
    affiliation = request.form['affiliation']
    organization = request.form['organization']
    today = date.today()
    d = today.strftime("%b-%d-%Y")
    info = "{}\n{}\n{}\n{}\n".format(str(d), str(country), str(affiliation), str(organization))
    save(info)
    return render_template('thanks_page.html')

def save(text, filepath="user_info.txt"):
    with open("user_info.txt", "a+") as f:
        f.write(text)

if __name__ == '__main__':
    app.run()