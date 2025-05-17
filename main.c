#include <stdio.h>
#include "gem5/m5ops.h"

int main() {
  m5_reset_stats(0, 0);
//  int a = -2;
//  int b = -4;
//  int c = a * b;
//  printf("%d\n", c);

//  uint32_t chunk;
//  uint32_t left = 1024;
//  uint32_t right = 2048;
//  uint64_t chunk;
//  uint64_t left = 1024;
//  uint64_t right = 2048;
//
//  chunk = ((uint64_t)left << 32) | right;
//  int c = a << 24 | b;


  int x = -4;
  int y = 2;
  int z = 5;

  int mul = x * y;
  mul = x * y;
  mul = x * y;
  mul = x * y;
  int mul2 = x * mul;

  int shift = x << y;

  int bor = x | y;

  int band = x & z;

  m5_dump_stats(0, 0);

  printf("Multiplication of %d and %d gives: %d\n", x, y, mul);
  printf("Multiplication of %d and %d gives: %d\n", x, mul, mul2);
  printf("Shift of %d and %d gives: %d\n", x, y, shift);
  printf("Bitwise OR of %d and %d results in: %d\n", x, y, bor);
  printf("Bitwise AND of %d and %d results in: %d\n", x, z, band);


  return 0;
}
