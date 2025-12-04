// matmul_3x2_2x3_neg.c - Multiply (3x2) × (2x3) = (3x3) with negatives
#include <stdio.h>
#include "gem5/m5ops.h"

void matmul(int A[3][2], int B[2][3], int C[3][3]) {
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      int sum = 0;
      for (int k = 0; k < 2; k++) {
        sum += A[i][k] * B[k][j];
      }
      C[i][j] = sum;
    }
  }
}

void print_matrix_3x3(int C[3][3]) {
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      printf("%5d ", C[i][j]);
    }
    printf("\n");
  }
}

int main(void) {
  m5_reset_stats(0, 0);
  int A[3][2] = {
    {  1, -2},
    { -3,  4},
    {  5, -6}
  };

  int B[2][3] = {
    {  7, -8,  9},
    { -10, 11, -12}
  };

  int C[3][3]; // Result

  matmul(A, B, C);

  printf("Matrix A (3x2):\n");
  for (int i = 0; i < 3; i++) {
    printf("%5d %5d\n", A[i][0], A[i][1]);
  }

  printf("\nMatrix B (2x3):\n");
  for (int i = 0; i < 2; i++) {
    printf("%5d %5d %5d\n", B[i][0], B[i][1], B[i][2]);
  }

  printf("\nResult C = A × B (3x3):\n");
  print_matrix_3x3(C);

  return 0;
}
