package com.galacredit.app;

final class ApiException extends Exception {
    final int statusCode;

    ApiException(int statusCode, String message) {
        super(message);
        this.statusCode = statusCode;
    }
}
