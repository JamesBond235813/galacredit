package com.juxin.xiaohebao.admin;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;

public final class ApkInstallProvider extends ContentProvider {
    static final String AUTHORITY = "com.juxin.xiaohebao.admin.apkprovider";
    private static final String MIME_APK = "application/vnd.android.package-archive";

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public String getType(Uri uri) {
        return MIME_APK;
    }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        if (getContext() == null || mode == null || mode.contains("w")) {
            throw new FileNotFoundException("不支持的安装文件访问");
        }
        File updatesDir = new File(getContext().getCacheDir(), "xhb-updates");
        File apk = new File(updatesDir, uri.getLastPathSegment() == null ? "" : uri.getLastPathSegment());
        try {
            String root = updatesDir.getCanonicalPath();
            String target = apk.getCanonicalPath();
            if (!target.startsWith(root + File.separator) || !apk.isFile()) {
                throw new FileNotFoundException("安装文件不存在");
            }
        } catch (IOException error) {
            throw new FileNotFoundException("安装文件不可用");
        }
        return ParcelFileDescriptor.open(apk, ParcelFileDescriptor.MODE_READ_ONLY);
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) {
        return null;
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        return null;
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        return 0;
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        return 0;
    }
}
