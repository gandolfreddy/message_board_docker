import boto3, botocore
from decouple import config as cfg
from flask import *
import mysql.connector.pooling
import os
from werkzeug.utils import secure_filename


CONFIG = {
    "user": cfg("MYSQLUSER"),
    "password": cfg("PASSWORD"),
    "host": cfg("HOST"),
    "database": cfg("DATABASE")
}

cnx_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name = "mypool",
    pool_size = 5,
    **CONFIG
)

UPLOAD_FOLDER = "static/files"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

## AWS S3 bucket settings
## e.g. https://wehelpbucket.s3.amazonaws.com/notion-avatar-1633667244492.png
S3_BUCKET = cfg("S3_BUCKET")
S3_LOCATION = f"https://{S3_BUCKET}.s3.amazonaws.com/"
CLOUDFRONT_DOMAIN = cfg("CLOUDFRONT_DOMAIN")
s3 = boto3.client(
    "s3",
    aws_access_key_id=cfg("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=cfg("AWS_SECRET_ACCESS_KEY"),
)


def query(cmd, content):
    try:
        cnx = cnx_pool.get_connection()
        cursor = cnx.cursor()
        cursor.execute(cmd, content)
        return cursor.fetchall()
    finally:
        if cnx.is_connected():
            cursor.close()
        if cnx:
            cnx.close()


def update(cmd, content):
    update_result = False
    try:
        cnx = cnx_pool.get_connection()
        cursor = cnx.cursor()
        cursor.execute(cmd, content)
        cnx.commit()
        update_result = True
    except:
        cnx.rollback()
    finally:
        if cnx.is_connected():
            cursor.close()
        if cnx:
            cnx.close()
        return update_result


def upload_file_to_s3(file, bucket_name):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={'ContentType': file.content_type}
        )
    except Exception as e:
        return f"upload file {file.filename} failed! {e}"

    return f"{CLOUDFRONT_DOMAIN}{file.filename}"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/getNshow", methods=["GET"])
def get_msg():
    query_cmd = '''
        SELECT content, img FROM msgrecord order by id desc;
    ''' 
    query_results = query(query_cmd, {})
    query_results = list(map(list, query_results))
    res = {"data": query_results}
    return jsonify(res)


@app.route("/api/submitNshow", methods=["POST"])
def submit_n_show():
    if request.method == "POST":
        ## check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        ## If the user does not select a file,
        ## the browser submits an empty file without a filename.
        if file.filename == '':
            flash("No selected file")
            return redirect(request.url)

        content = request.form["content"]
        if content and file and allowed_file(file.filename):
            file.filename = secure_filename(file.filename)
            ## save to local
            # file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
            img = upload_file_to_s3(file, S3_BUCKET)
            
            insert_cmd = '''
            INSERT INTO msgrecord (content, img) 
                        values (%(content)s, %(img)s);
            ''' 
            insert_content = {
                "content": content,
                "img": img
            }
            update_result = update(insert_cmd, insert_content)
            if update_result:
                query_cmd = '''
                    select content, img from msgrecord order by id desc limit 0, 1;
                ''' 
                query_results = query(query_cmd, {})
                query_results = list(map(list, query_results))
                res = {"data": query_results}
                return jsonify(res)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
