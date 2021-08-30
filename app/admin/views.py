from flask import Blueprint, render_template


admin = Blueprint('admin', __name__,
                     template_folder='templates',
                     static_folder='templates/html',
                     static_url_path='')


@admin.route('/')
def index():
    return render_template('index.html')


@admin.route('/user_interface')
def userUI():
    return render_template('user_interface.html')

