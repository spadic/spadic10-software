#include <stdio.h>
#include "message_reader.c"

void print_queue(struct buf_queue q)
{
    printf("-> begin: %d  end: %d  empty: %s\n",
        q.begin ? q.begin->len : 0,
        q.end ? q.end->len : 0,
        buf_queue_is_empty(&q) ? "yes" : "no");
}

int main(void)
{
    struct buf_queue q;
    buf_queue_init(&q);

    struct buf_item a, b, c, *d;
    a.len = 1;
    b.len = 2;
    c.len = 3;

    printf("init\n");
    print_queue(q);
    printf("append 1\n");
    buf_queue_append(&q, &a);
    print_queue(q);
    printf("append 2\n");
    buf_queue_append(&q, &b);
    print_queue(q);
    printf("pop:");
    d = buf_queue_pop(&q);
    printf(" %d\n", d ? d->len : 0);
    print_queue(q);
    printf("append 3\n");
    buf_queue_append(&q, &c);
    print_queue(q);
    printf("pop:"); /* 2 */
    d = buf_queue_pop(&q);
    printf(" %d\n", d ? d->len : 0);
    print_queue(q);
    printf("pop:"); /* 3 */
    d = buf_queue_pop(&q);
    printf(" %d\n", d ? d->len : 0);
    print_queue(q);
    printf("pop:");
    d = buf_queue_pop(&q);
    printf(" %d\n", d ? d->len : 0);
    print_queue(q);
    printf("pop:");
    d = buf_queue_pop(&q);
    printf(" %d\n", d ? d->len : 0);
    print_queue(q);
    printf("append 1\n");
    buf_queue_append(&q, &a);
    print_queue(q);

    return 0;
}
