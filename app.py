from flask import Flask, render_template, request, redirect, jsonify, session
import pyodbc
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 设置一个真正安全的密钥，替换示例中的字符串
# 数据库连接字符串，根据实际情况修改
conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    r"DBQ=C:\Database\Database1.accdb;"
)


# 首页路由，获取当前用户的笔记并展示
@app.route('/')
def index():
    if 'user_id' in session:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT *, TimeStamp AS saved_time FROM Notes WHERE user_id =? ORDER BY order_num",
                           (session['user_id'],))
            notes = cursor.fetchall()
        except pyodbc.Error as e:
            print("Error occurred when performing DB operation: ", e)
            notes = []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        return render_template('index.html', notes=notes)
    return redirect('/login')


# 用户注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            # 插入新用户信息，默认不是管理员
            cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()
            return redirect('/login')
        except pyodbc.Error as e:
            print("Error occurred during registration: ", e)
            return "Registration failed. Please try again."
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return render_template('register.html')


# 用户登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username =? AND password =?", (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                session['is_admin'] = bool(user[3])
                return redirect('/')
            else:
                return "Invalid username or password"
        except pyodbc.Error as e:
            print("Error occurred during login: ", e)
            return "Login failed. Please try again."
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return render_template('login.html')


# 用户登出路由
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect('/login')


# 添加笔记路由，新增关联当前登录用户的逻辑
@app.route('/add', methods=['POST'])
def add_note():
    if 'user_id' in session:
        content = request.form['content']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Notes (content, user_id) VALUES (?,?)",
                           (content, session['user_id']))
            # 假设新添加的笔记默认顺序为最后（可以根据实际需求调整初始顺序逻辑）
            cursor.execute("SELECT MAX(order_num) FROM Notes WHERE user_id =?", (session['user_id'],))
            max_order_num = cursor.fetchone()[0]
            if max_order_num is None:
                new_order_num = 1
            else:
                new_order_num = max_order_num + 1
            cursor.execute("UPDATE Notes SET order_num =? WHERE id = (SELECT MAX(id) FROM Notes WHERE user_id =?)",
                           (new_order_num, session['user_id']))
            cursor.execute("UPDATE Notes SET color_tag = 'green' WHERE id = (SELECT MAX(id) FROM Notes WHERE user_id =?)",
                           (session['user_id'],))
            conn.commit()
        except pyodbc.Error as e:
            print("Error occurred when inserting data: ", e)
            print("The SQL statement is: ", "INSERT INTO Notes (content, TimeStamp) VALUES (?,?)")
            print("The inserted content value is: ", content)
            print("The inserted time value is: ", current_time)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        return redirect('/')
    return redirect('/login')


# 编辑笔记页面路由
@app.route('/edit/<int:note_id>', methods=['GET'])
def edit_note(note_id):
    if 'user_id' in session:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Notes WHERE id =? AND user_id =?", (note_id, session['user_id']))
            note = cursor.fetchone()
            if note:
                return render_template('edit.html', note=note)
            else:
                return redirect('/')
        except pyodbc.Error as e:
            print("Error occurred when retrieving note for editing: ", e)
            return redirect('/')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return redirect('/login')


# 处理编辑笔记表单提交路由
@app.route('/edit/<int:note_id>', methods=['POST'])
def update_note(note_id):
    if 'user_id' in session:
        updated_content = request.form['content']
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("UPDATE Notes SET content =? WHERE id =? AND user_id =?",
                           (updated_content, note_id, session['user_id']))
            conn.commit()
        except pyodbc.Error as e:
            print("Error occurred when updating the note: ", e)
            return redirect('/')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        return redirect('/')
    return redirect('/login')


# 删除笔记确认页面路由
@app.route('/delete/<int:note_id>', methods=['GET'])
def delete_confirm(note_id):
    if 'user_id' in session:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Notes WHERE id =? AND user_id =?", (note_id, session['user_id']))
            note = cursor.fetchone()
            if note:
                return render_template('delete.html', note=note)
            else:
                return redirect('/')
        except pyodbc.Error as e:
            print("Error occurred when retrieving note for deletion confirmation: ", e)
            return redirect('/')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return redirect('/login')


# 实际删除笔记路由
@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' in session:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Notes WHERE id =? AND user_id =?", (note_id, session['user_id']))
            conn.commit()
        except pyodbc.Error as e:
            print("Error occurred when deleting the note: ", e)
            return redirect('/')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        return redirect('/')
    return redirect('/login')


# 更新笔记顺序路由
@app.route('/update_order', methods=['POST'])
def update_order():
    if 'user_id' in session:
        try:
            new_order = request.get_json()
            if not isinstance(new_order, list):
                return jsonify({"error": "Invalid data format"}), 400

            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            for index, note_id in enumerate(new_order):
                cursor.execute("UPDATE Notes SET order_num =? WHERE id =? AND user_id =?",
                               (index + 1, note_id, session['user_id']))

            conn.commit()
            return jsonify({"message": "Order updated successfully"})
        except pyodbc.Error as e:
            print("Error occurred when updating the note order: ", e)
            return jsonify({"error": "Failed to update order"}), 500
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return redirect('/login')


# 更新笔记颜色标记路由
@app.route('/update_color', methods=['POST'])
def update_color():
    if 'user_id' in session:
        note_id = request.form['note_id']
        new_color_tag = request.form['new_color_tag']
        print(f"Received note_id: {note_id}, new_color_tag: {new_color_tag}")
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("UPDATE Notes SET color_tag =? WHERE id =? AND user_id =?",
                           (new_color_tag, note_id, session['user_id']))
            print("Executed SQL statement successfully")
            conn.commit()
        except pyodbc.Error as e:
            print("Error occurred when updating the note color tag: ", e)
            print("The SQL statement is: ", "UPDATE Notes SET color_tag =? WHERE id =? AND user_id =?",
                  (new_color_tag, note_id, session['user_id']))
            return redirect('/')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        return redirect('/')
    return redirect('/login')


# 用户管理路由，只有管理员能访问，展示用户列表
@app.route('/userManagement', methods=['GET'])
def userManagement():
    if 'is_admin' in session and session['is_admin']:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            return render_template('userManagement.html', users=users)
        except pyodbc.Error as e:
            print("Error occurred when retrieving users for management: ", e)
            return redirect('/')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return redirect('/')


# 设置用户为管理员的路由
@app.route('/set_admin/<int:user_id>', methods=['POST'])
def set_admin(user_id):
    if 'is_admin' in session and session['is_admin']:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_admin = 1 WHERE id =?", (user_id,))
            conn.commit()
            return redirect('/userManagement')
        except pyodbc.Error as e:
            print("Error occurred when setting user as admin: ", e)
            return redirect('/userManagement')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return redirect('/')


# 取消用户管理员权限的路由
@app.route('/remove_admin/<int:user_id>', methods=['POST'])
def remove_admin(user_id):
    if 'is_admin' in session and session['is_admin']:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_admin = 0 WHERE id =?", (user_id,))
            conn.commit()
            return redirect('/userManagement')
        except pyodbc.Error as e:
            print("Error occurred when removing user's admin privileges: ", e)
            return redirect('/userManagement')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return redirect('/')


if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)