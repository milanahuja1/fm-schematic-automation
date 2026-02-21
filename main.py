import turtle

def draw_square(t, size):
    for _ in range(4):
        t.forward(size)
        t.right(90)

screen = turtle.Screen()
t = turtle.Turtle()

draw_square(t, 100)

t.penup()
t.goto(150, 0)
t.pendown()

draw_square(t, 50)

screen.mainloop()