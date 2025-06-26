import os
import gzip
from datetime import datetime, timedelta
from ftplib import FTP
import subprocess

def convert_date_format(date_str):
    try:
        if len(date_str) == 10 and date_str.count('-') == 2:#YYYY-MM-DD（标准日期格式）
            return date_str
        elif len(date_str) == 8 and date_str.count('-') == 1:#YYYY-DOY（年和年积日）
            year = int(date_str[:4])
            doy = int(date_str[5:])
            return (datetime(year, 1, 1) + timedelta(days=doy - 1)).strftime("%Y-%m-%d")
        elif len(date_str) == 5 and date_str.isdigit():#MJD（Modified Julian Date）
            mjd_start = datetime(1858, 11, 17)
            return (mjd_start + timedelta(days=int(date_str))).strftime("%Y-%m-%d")
        elif len(date_str.split('_')) == 2:#GPS 周和天格式(123_5)
            week, day = map(int, date_str.split('_'))
            gps_start = datetime(1980, 1, 6)
            return (gps_start + timedelta(weeks=week, days=day)).strftime("%Y-%m-%d")
        else:
            raise ValueError("Unsupported date format")
    except Exception as e:
        print(f"Error converting date: {e}")
        raise

def generate_igs_url(station, date, interval, version):
    year = date[:4]
    doy = str((datetime.strptime(date, "%Y-%m-%d") - datetime(int(year), 1, 1)).days + 1).zfill(3)
    
    if version == "rinex3":
        folder = "30S" if interval == "30s" else "1S"
        extension = ".crx.gz"
        filename = f"{station}_R_{year}{doy}0000_01D_{folder}_MO{extension}"
    else:  # RINEX 2 format
        short_year = year[-2:] 
        filename = f"{station}{doy}0.{short_year}d.gz"
    
    return f"pub/igs/data/{year}/{doy}/{filename}"

def download_file(ftp, url):
    local_filename = url.split('/')[-1]
    with open(local_filename, 'wb') as f:
        ftp.retrbinary(f'RETR {url}', f.write)
    return local_filename

def decompress_file(file_name):
    with gzip.open(file_name, 'rb') as f_in:
        new_file_name = file_name.replace('.gz', '')
        with open(new_file_name, 'wb') as f_out:
            f_out.write(f_in.read())
    os.remove(file_name)
    return new_file_name

def convert_crx_to_rnx(crx_file):
    crx_file_abs_path = os.path.abspath(crx_file)
    if not os.path.exists(crx_file_abs_path):
        return
    try:
        subprocess.run(
            ["D:/RNXCMP_4.1.0_Windows_mingw_32bit/bin/crx2rnx", crx_file_abs_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        os.remove(crx_file_abs_path)
        print(f"Successfully converted {crx_file_abs_path}")
    except subprocess.CalledProcessError:
        print(f"Failed to convert {crx_file_abs_path}")

def convert_d_to_o(d_file):
    d_file_abs_path = os.path.abspath(d_file)
    if not os.path.exists(d_file_abs_path):
        return
    try:
        subprocess.run(
            ["D:/RNXCMP_4.1.0_Windows_mingw_32bit/bin/crx2rnx", d_file_abs_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        os.remove(d_file_abs_path)
        print(f"Successfully converted {d_file_abs_path} ")
    except subprocess.CalledProcessError:
        print(f"Failed to convert {d_file_abs_path} ")

def main(start_date, end_date, interval, version, stations):
    start_date = convert_date_format(start_date)
    end_date = convert_date_format(end_date)
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    current = start

    # 连接到FTP服务器
    ftp = FTP('igs.ign.fr')
    ftp.login()

    while current <= end:
        for station in stations:
            url = generate_igs_url(station, current.strftime("%Y-%m-%d"), interval, version)
            print(f"Downloading {url}")
            try:
                file_name = download_file(ftp, url)
                decompressed_file = decompress_file(file_name)

                if version == "rinex2":
                    convert_d_to_o(decompressed_file) 
                elif version == "rinex3":
                    convert_crx_to_rnx(decompressed_file)

            except Exception as e:
                print(f"Failed to download {url}: {e}")
        current += timedelta(days=1)

    ftp.quit()

if __name__ == "__main__":
    start_date = input("请输入开始时间 (格式: yyyy-mm-dd, yyyy-doy, GPS周_天, 或MJD): ")
    end_date = input("请输入结束时间 (格式: yyyy-mm-dd, yyyy-doy, GPS周_天, 或MJD): ")
    interval = input("请选择时间间隔 (30s 或 1s): ")
    version = input("请选择RINEX版本 (rinex2 或 rinex3): ")
    stations_input = input("请输入IGS站点 (例如: AUHI,BKPS,GOLD,HERA): ")
    stations = [station.strip() for station in stations_input.split(',')]
    try:
        main(start_date, end_date, interval, version, stations)
    except ValueError as e:
        print(e)
