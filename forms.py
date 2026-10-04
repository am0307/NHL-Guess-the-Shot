from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL

# Registration form for new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()], render_kw={"placeholder": "Enter your email"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"placeholder": "Create a password"})
    verify_password = PasswordField("Verify Password", validators=[DataRequired()], render_kw={"placeholder": "Verify your password"})
    submit = SubmitField("Register")

# Login form for existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()], render_kw={"placeholder": "Enter your email"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"placeholder": "Enter your password"})
    submit = SubmitField("Login")