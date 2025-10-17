from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import dropbox
import os
from dropbox.exceptions import ApiError, AuthError
import traceback

app = Flask(__name__)
app.secret_key = '9lfgpuc1xlzpbrp'

DROPBOX_ACCESS_TOKEN = 'sl.u.AGDjCEh7Jy838mKhxsXpe89olYxS9AQC2dZN_rZ_RkoUD5mBBKoiGz7EdBYJsOBtSbnje5Lj4LspjfYY7Fon2WMayW7QH5pVTpN9tREq6Tn1-a4RnfWSC_wjtp9XiYt1Bucaz__AqcKCGel4mZg-vjhh_MrwLdPIw43b0vyELTXkDZC1Abj6Jvs3qh5YGa2L_JcPDBnlB2RPwu-VZ9LsC6XWwvpe7C5v68Tbx4RfOTLNW8f-eI4Y-7iCpid5svVeTn0XYOIOKdL3RPzs8Kp2MQYHJnZhKV1O22swUBT06mF1k0LD5WPS1mvg0Fvm4VfzNa0Ucv6GlUVv0krjdgCBWYA_owQyQwfLZssGGbxQ5pnPGZoPjE6O2VsCz_OO3XqAHtX5Xes5p9PTjZNDrSkweKR3OdF33UThdFT2i1KlRBSCqc8jVRRebxGEDhnKlFwncOSUW16NagPfjo_46aEnJdnSoIG5JluqVfgUHw6-9HBPtQMy8EGVtRWnFS_qEvC8jg7ZWbeoRmY4561nMG0ZjhzwxlUFpUwZQwmbt8F3GP4Hlc2nnzLKdw1gKFZrwpju7FjROCWGPsZh8YfzI9HWb5qiSL5J2y15R1TcqOMCFv0xSmv2huyTIW7nhBPyEekMRi2VFGKqfOxxggq-yNJ-MwKx13c_YDGloYx4LIjrCgFupv7e3EEJhZuQPhS1Z7D8lutOdmj-OVaqZ3lSeVrAJty8YZpMrejDG4aHt9Syam2-IItRXZGPGnN74BgS3Fi5yrgypofLANyb64UsVK_c9Uz8_5fwIjdpde2FFk5NuF0zR1mb1fFWwJixOAz9m0He-5uom0-1lXFxrVx5qu0gnwtFyFJzoJA9vlzQnFqywlxWDGD3sJ9P3s5J9D8CwqQ9oe4EvnjO8ap3mPYXBTuOWeaN6zfvveBPKqBVDr2LNJ5wto9YImrhGbL_Y3DtmrmD8CDEvx2lr95XhyeEVMUudWRGIPnUTjcZ5Uj3ta522diqp5e0Dc8AyGvh143sLEKfaobcGWBSOgit9UO7INLiX9Lhw-B861_PjsrVmP4hfOOZxuKa45erO4egtRSz8pHR0BiFPKSBuW28kcTQB7UXdtS14CbxDNo4Z2R0OF-27RUH8JHLHgB4hFCdC9ENLhIgE_2Z6b5eV47PoDUH2Lm3WJN_7jW0zOROBRXtqvIzlaay-QID4945PSE-N0vxVnbifNdrhIp2Yn1RBxzGic_5-jVMPardcSjQtr59sLejIq-fvmtB6y7Jp67cysdT7yQWKrxaTJjORsRSbGEY1dABlDssbi3UDAL5QrccWHsKw_RI3yBq2R3tC9LhaEHCyVOTxMqZpXwcVDMAa5UDO1vg-h0xlNBa9SHmb6bcDiS7RFd1kywnsCgvVBLgs5aFeSMxhoN_uUVMFTGw2q87uK2CpaCRD68xWZrkX5ru00LGm_GuQA'

# Initialize Dropbox client
try:
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    account = dbx.users_get_current_account()
    print(f"✅ Connected to Dropbox as: {account.name.display_name}")
    DROPBOX_CONNECTED = True
except Exception as e:
    print(f"❌ Dropbox connection failed: {e}")
    dbx = None
    DROPBOX_CONNECTED = False

def get_dropbox_files():
    """Get list of files from Dropbox"""
    if not dbx:
        return []
    
    try:
        result = dbx.files_list_folder("")
        files = []
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                files.append({
                    'name': entry.name,
                    'size': entry.size,
                    'path': entry.path_lower
                })
        return files
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

@app.route('/')
def index():
    files = get_dropbox_files() if DROPBOX_CONNECTED else []
    return render_template('index.html', files=files, connected=DROPBOX_CONNECTED, dbx=DROPBOX_CONNECTED)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not dbx:
        flash("❌ Dropbox connection failed. Please check your access token.", "error")
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        flash("❌ No file part in the request.", "error")
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash("❌ No file selected.", "error")
        return redirect(url_for('index'))
    
    try:
        file_data = file.read()
        file_name = file.filename
        
        # Sanitize filename
        file_name = file_name.replace('\\', '/').split('/')[-1]
        dropbox_path = f"/{file_name}"
        
        print(f"📤 Uploading: {file_name} to {dropbox_path}")
        
        # Upload to Dropbox
        result = dbx.files_upload(file_data, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        
        flash(f"✅ File '{file_name}' uploaded successfully to Dropbox!", "success")
        
    except ApiError as e:
        flash(f"❌ Dropbox API error: {e}", "error")
    except Exception as e:
        flash(f"❌ Unexpected error: {str(e)}", "error")
        print(traceback.format_exc())
    
    return redirect(url_for('index'))

@app.route('/download', methods=['POST'])
def download_file():
    if not dbx:
        flash("❌ Dropbox connection failed.", "error")
        return redirect(url_for('index'))
    
    filename = request.form['filename']
    if not filename:
        flash("❌ Please enter a filename.", "error")
        return redirect(url_for('index'))
    
    filename = filename.strip()
    dropbox_path = f"/{filename}"
    local_path = os.path.join("downloads", filename)

    os.makedirs("downloads", exist_ok=True)

    try:
        dbx.files_download_to_file(local_path, dropbox_path)
        
        if os.path.exists(local_path):
            response = send_file(local_path, as_attachment=True, download_name=filename)
            
            @response.call_on_close
            def remove_file():
                try:
                    os.remove(local_path)
                except:
                    pass
                    
            return response
        else:
            flash("❌ Download failed.", "error")
            
    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            flash(f"❌ File '{filename}' not found in Dropbox.", "error")
        else:
            flash(f"❌ Dropbox API error: {e}", "error")
    except Exception as e:
        flash(f"❌ Error downloading file: {str(e)}", "error")
    
    return redirect(url_for('index'))

@app.route('/list')
def list_files():
    """Debug endpoint to list files"""
    if not dbx:
        return "Dropbox not connected"
    
    try:
        files = get_dropbox_files()
        if files:
            file_list = "<br>".join([f"{f['name']} ({f['size']} bytes)" for f in files])
            return f"Files in Dropbox:<br>{file_list}"
        else:
            return "No files found in Dropbox"
    except Exception as e:
        return f"Error: {e}"

@app.route('/refresh')
def refresh_files():
    """Refresh the file list"""
    files = get_dropbox_files()
    return jsonify(files)

if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    print("🚀 Starting Flask application...")
    print("📝 Visit http://localhost:5000 to access the application")
    app.run(debug=True)