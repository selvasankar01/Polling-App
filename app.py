from flask import Flask, request , redirect,render_template, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

# global variable
logged = False

connector = db.Table('connector',
    db.Column('login_id',db.Integer,db.ForeignKey('login.id'),primary_key=True),
    db.Column('teams_id',db.Integer,db.ForeignKey('teams.id'),primary_key=True)
)

multiple_admin = db.Table('multiple_admin',
    db.Column('login_id',db.Integer,db.ForeignKey('login.id')),
    db.Column('teams_id',db.Integer,db.ForeignKey('teams.id'))
)

class Login(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),nullable=False,unique=True)
    password = db.Column(db.String(20),nullable=False)
    team_owner = db.Column(db.Integer,db.ForeignKey('teams.id'))
    teams_list = db.relationship('Teams', secondary=connector, backref=db.backref('members', lazy=True))

    def __repr__(self):
        return f'id = {self.id}, username = {self.username}'

class Teams(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(30),nullable=False,unique=True)
    polls_list = db.Column(db.Integer,db.ForeignKey('poll_info.id'))
    admin = db.relationship('Login',secondary=multiple_admin, backref = db.backref('team_admins',lazy='select'))

    def __repr__(self):
        return f'id = {self.id}, TeamName = {self.name}, admin = {self.admin}, members = {self.members}'

class PollInfo(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    team = db.relationship('Teams',backref=db.backref('polls_in_team',lazy='select'))

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        try:
            userid = request.form['username']
            pasword = request.form['password']
            user = Login.query.filter_by(username = userid).first().id
            pword = Login.query.get(user)
            if pasword == pword.password:
                global logged 
                logged = True
                return redirect(f'/{userid}')
            else:
                return render_template('login.html',login='Wrong input credentials')
        except:
            return render_template('login.html',login='Account doesn"t exists')
    else:    
        return render_template('login.html',login=False)

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        userid = request.form['username']
        pasword = request.form['password']
        confirmpasword = request.form['confirmpassword']
        if Login.query.filter_by(username=userid).first():
            return render_template('register.html',value='This username already exists')
        elif pasword == confirmpasword:
            user = Login(username = userid, password = pasword)
            try:
                db.session.add(user)
                db.session.commit()
                return redirect(f'/login')
            except:
                return f"Couldn't create account try again later"
        else:
            return render_template('register.html',value='Confirm password is different from password')
    else:
        return render_template('register.html',value=False)


@app.route('/<user_name>')
def mainpage(user_name):
    global logged
    if logged:
        logged = False
        usr = Login.query.filter_by(username=user_name).first()
        in_teams = usr.teams_list
        return render_template('mainpage.html',teams=in_teams,user=user_name)
    else:
        return redirect('/login')


@app.route('/<user>/team/create',methods=['GET','POST'])
def create_team(user):
    if request.method == 'POST':
        team_name = request.form['teamname']
        usr = Login.query.filter_by(username=user).first()
        if Teams.query.filter_by(name = team_name).first():
            return render_template('mainpage.html',result = 'Team name already exists')
        else:
            new_team = Teams(name=team_name)
            try:
                db.session.add(new_team)
                new_team.admin.append(usr)
                new_team.members.append(usr)
                db.session.commit()
                return redirect(f'/{user}/{team_name}/add')
            except:
                return 'Couldn\'t create team. Try again.'
    else:
        return redirect(f'/{user}')

@app.route('/<user>/<teamname>/add',methods=['GET','POST'])
def add_member(teamname,user):
    if request.method == 'POST':
        new_member = request.form['newmember']
        team_name = Teams.query.filter_by(name=teamname).first()
        is_user = Login.query.filter_by(username=new_member).first()
        team_admin_list = team_name.admin
        for member in team_admin_list:
            if member == user:
                role = request.form['role']
                if is_user:
                    team_name.members.append(is_user)
                    if role == 'admin':
                        team_name.admin.appen(is_user)
                    db.session.commit()
                    return render_template('addmember.html', user=is_user ,team = team_name.members,result='User is registered')
                else:
                    return render_template('addmember.html', user=is_user, team = team_name.members,result='User is not registered')
        else:
            return render_template('addmember.html', user=is_user, team = team_name.members,result='Only admin could add members')
    else:
        return render_template('addmember.html', user=Login.query.filter_by(username=user).first(),team = Teams.query.filter_by(name=teamname).first().members,result='Add members to the team')

@app.route('/<user>/<teamname>/feed')
def feed(user,teamname):
    team = Teams.query.filter_by(name=teamname).first()
    mem = team.members
    feed = team.polls_in_team
    if user in team.admin:
        return render_template('feed.html',members = mem,feeds = feed,admin=True)
    else:
        return render_template('feed.html',members = mem,feeds = feed,admin=False)

if __name__ == '__main__':
    app.run(debug=True)