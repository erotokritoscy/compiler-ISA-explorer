// poly_mul.c - Polynomial multiplication in C (integer coefficients)
#include <stdio.h>
#include "gem5/m5ops.h"


// Multiply polynomials A (deg m-1) and B (deg n-1), result in C (deg m+n-2)
void poly_mul(int m, int n, int A[m], int B[n], int C[m+n-1]) {
  // Initialize result with zeros
  for (int i = 0; i < m + n - 1; i++) {
    C[i] = 0;
  }

  // Multiply
  for (int i = 0; i < m; i++) {
    for (int j = 0; j < n; j++) {
      C[i + j] += A[i] * B[j];
    }
  }
}

// Print polynomial as human-readable form
void print_poly(int deg, int P[]) {
  for (int i = 0; i <= deg; i++) {
    int coeff = P[i];
    if (coeff == 0) continue;

    if (i > 0 && coeff > 0) printf(" + ");
    if (coeff < 0) printf(" - ");

    int abs_coeff = coeff < 0 ? -coeff : coeff;
    if (abs_coeff != 1 || i == 0) printf("%d", abs_coeff);

    if (i > 0) {
      printf("x");
      if (i > 1) printf("^%d", i);
    }
  }
  printf("\n");
}

int main(void) {
  // Example: (1 + 2x + 3x^2) * (4 + 5x)
  m5_reset_stats(0, 0);

  int A[3] = {1, 2, 3};  // degree 2
  int B[2] = {4, 5};     // degree 1
  int C[4];              // degree 3 (2+1)

  poly_mul(3, 2, A, B, C);
  m5_dump_stats(0, 0);

  printf("A(x) = ");
  print_poly(2, A);

  printf("B(x) = ");
  print_poly(1, B);

  printf("C(x) = A(x)*B(x) = ");
  print_poly(3, C);

  return 0;
}
