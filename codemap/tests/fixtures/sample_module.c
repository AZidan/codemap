/**
 * Sample C module for testing the C parser.
 * Demonstrates structs, enums, functions, and typedefs.
 */

#include <stdio.h>
#include <stdlib.h>

/* Status codes for operations */
enum Status {
    STATUS_OK = 0,
    STATUS_ERROR = -1,
    STATUS_PENDING = 1
};

/* Represents a 2D point */
struct Point {
    int x;
    int y;
};

/* Represents a rectangle with two points */
struct Rectangle {
    struct Point top_left;
    struct Point bottom_right;
};

/* Callback function type */
typedef void (*EventCallback)(int event_id, void* data);

/* Type alias for byte */
typedef unsigned char byte;

/* Type alias for status */
typedef enum Status StatusCode;

/**
 * Add two integers.
 * @param a First operand
 * @param b Second operand
 * @return Sum of a and b
 */
int add(int a, int b) {
    return a + b;
}

/**
 * Subtract two integers.
 */
int subtract(int a, int b) {
    return a - b;
}

/* Create a new point */
struct Point create_point(int x, int y) {
    struct Point p;
    p.x = x;
    p.y = y;
    return p;
}

/* Calculate distance squared between two points */
int distance_squared(struct Point p1, struct Point p2) {
    int dx = p2.x - p1.x;
    int dy = p2.y - p1.y;
    return dx * dx + dy * dy;
}

/* Check if a point is inside a rectangle */
int point_in_rect(struct Point p, struct Rectangle rect) {
    return p.x >= rect.top_left.x &&
           p.x <= rect.bottom_right.x &&
           p.y >= rect.top_left.y &&
           p.y <= rect.bottom_right.y;
}

/**
 * Allocate and initialize a new array.
 * @param size Number of elements
 * @return Pointer to allocated array or NULL on failure
 */
int* create_array(size_t size) {
    int* arr = (int*)malloc(size * sizeof(int));
    if (arr == NULL) {
        return NULL;
    }
    for (size_t i = 0; i < size; i++) {
        arr[i] = 0;
    }
    return arr;
}

/* Free an array */
void free_array(int* arr) {
    if (arr != NULL) {
        free(arr);
    }
}

/* Print a point to stdout */
void print_point(struct Point p) {
    printf("Point(%d, %d)\n", p.x, p.y);
}

/* Main entry point */
int main(int argc, char* argv[]) {
    struct Point p = create_point(10, 20);
    print_point(p);

    int sum = add(5, 3);
    printf("Sum: %d\n", sum);

    return STATUS_OK;
}
