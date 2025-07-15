#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "gem5/m5ops.h"

/* Constants from Blowfish algorithm initialized using hex digits of pi */
typedef unsigned char          uint8_t;
typedef unsigned int           uint32_t;
typedef unsigned long long int uint64_t;

/* Macro for swapping values */
#define SWAP(x, y, temp) {temp = (x); (x) = (y); (y) = temp;}

/* MUST NOT BE ALTERED */
#define KEYSIZE   56
#define DATASIZE  1024

/* Change these to alter the ciphertext and secret key */
#define PLAINTEXT "testing!"
#define KEY       "the key is you"

uint32_t sbox[4][256];
uint32_t pbox[18];

uint32_t init_sbox[4][256];  // Truncated for brevity
uint32_t init_pbox[18] = {
  0x243f6a88, 0x85a308d3, 0x13198a2e, 0x03707344, 0xa4093822, 0x299f31d0,
  0x082efa98, 0xec4e6c89, 0x452821e6, 0x38d01377, 0xbe5466cf, 0x34e90c6c,
  0xc0ac29b7, 0xc97c50dd, 0x3f84d5b5, 0xb5470917, 0x9216d5d9, 0x8979fb1b
};

/* Load initial constants (normally from Schneier's values) */
void init_constants() {
    memcpy(pbox, init_pbox, sizeof(init_pbox));
    // Fill sbox with your own init_sbox data here (omitted for brevity)
}

/* Feistel function used in encryption/decryption */
uint32_t feistel_function(uint32_t arg) {
    uint32_t var = sbox[0][arg >> 24] + sbox[1][(uint8_t)(arg >> 16)];
    return (var ^ sbox[2][(uint8_t)(arg >> 8)]) + sbox[3][(uint8_t)(arg)];
}

void _encrypt(uint32_t *left, uint32_t *right) {
    uint32_t i, t;
    for (i = 0; i < 16; i++) {
        *left ^= pbox[i];
        *right ^= feistel_function(*left);
        SWAP(*left, *right, t);
    }
    SWAP(*left, *right, t);
    *right ^= pbox[16];
    *left ^= pbox[17];
}

void _decrypt(uint32_t *left, uint32_t *right) {
    uint32_t i, t;
    for (i = 17; i > 1; i--) {
        *left ^= pbox[i];
        *right ^= feistel_function(*left);
        SWAP(*left, *right, t);
    }
    SWAP(*left, *right, t);
    *right ^= pbox[1];
    *left ^= pbox[0];
}

void blowfish_init(uint8_t key[], int size) {
    int keysize = size, i, j;
    uint32_t left = 0x00000000, right = 0x00000000;

    for (i = 0; i < 18; i++) {
        pbox[i] ^= ((uint32_t)key[(i + 0) % keysize] << 24) |
                   ((uint32_t)key[(i + 1) % keysize] << 16) |
                   ((uint32_t)key[(i + 2) % keysize] <<  8) |
                   ((uint32_t)key[(i + 3) % keysize]);
    }

    for (i = 0; i <= 17; i += 2) {
        _encrypt(&left, &right);
        pbox[i]     = left;
        pbox[i + 1] = right;
    }

    for (i = 0; i <= 3; i++) {
        for (j = 0; j <= 254; j += 2) {
            _encrypt(&left, &right);
            sbox[i][j]     = left;
            sbox[i][j + 1] = right;
        }
    }
}

uint8_t *blowfish_encrypt(uint8_t data[], int padsize) {
    uint8_t *encrypted = malloc(sizeof *encrypted * padsize);
    uint32_t i;
    uint32_t left, right;
    uint64_t chunk;

    for (i = 0; i < padsize; i += 8) {
        chunk = 0;
        memmove(&chunk, data + i, sizeof(chunk));
        left = chunk >> 32;
        right = chunk;

        _encrypt(&left, &right);

        chunk = ((uint64_t)left << 32) | right;
        memmove(encrypted + i, &chunk, sizeof(chunk));
    }
    return encrypted;
}

uint8_t *blowfish_decrypt(uint8_t crypt_data[], int padsize) {
    uint8_t *decrypted = malloc(sizeof *decrypted * padsize);
    uint32_t i;
    uint32_t left, right;
    uint64_t chunk;

    for (i = 0; i < padsize; i += 8) {
        chunk = 0;
        memmove(&chunk, crypt_data + i, sizeof(chunk));
        left = chunk >> 32;
        right = chunk;

        _decrypt(&left, &right);

        chunk = ((uint64_t)left << 32) | right;
        memmove(decrypted + i, &chunk, sizeof(chunk));
    }
    return decrypted;
}

int main() {
    m5_reset_stats(0, 0);

    int i, Osize, Psize, Pbyte;
    int KOsize, KPsize, KPbyte;
    uint8_t *encrypted, *decrypted, key[KEYSIZE], data[DATASIZE];

    memset(data, 0, DATASIZE);
    memset(key,  0, KEYSIZE);

    strncpy((char *)data, PLAINTEXT, sizeof(data));
    strncpy((char *)key, KEY, sizeof(key));

    Osize = strlen((char *)data);
    KOsize = strlen((char *)key);
    Psize = ((Osize + 7) / 8) * 8;
    KPsize = ((KOsize + 7) / 8) * 8;
    Pbyte = Psize - Osize;
    KPbyte = KPsize - KOsize;

    memset(data + Osize, Pbyte, sizeof *data * Pbyte);
    memset(key + KOsize, KPbyte, sizeof *key * KPbyte);

    init_constants();  // load initial values
    blowfish_init(key, KPsize);

    encrypted = blowfish_encrypt(data, Psize);

//    printf("encrypted data: ");
//    for (i = 0; i < Psize; i += 8) {
//        printf("%.2X%.2X%.2X%.2X ", encrypted[i], encrypted[i + 1],
//               encrypted[i + 2], encrypted[i + 3]);
//        printf("%.2X%.2X%.2X%.2X ", encrypted[i + 4], encrypted[i + 5],
//               encrypted[i + 6], encrypted[i + 7]);
//    }
//    printf("\n");

    decrypted = blowfish_decrypt(encrypted, Psize);
    m5_dump_stats(0, 0);

    memset(data, 0, Psize);
    memmove(data, decrypted, Osize);


    printf("decrypted data: %s\n", data);

    free(encrypted);
    free(decrypted);
    return 0;
}
