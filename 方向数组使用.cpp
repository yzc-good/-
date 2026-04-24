利用方向数组
int dx[N] = { 0,1,0,-1 };
int dy[N] = { 1,0,-1,0 };
和pos的结合就可以实现上、下、左、右的移位
//-----------------------------------------------------------------------------
题目描述：
给出一个不大于9的正整数n，输出n*n的蛇形方阵，从左上角填上1开始，顺时针方向依次填入数字
 例子：1  2  3  4
      12 13 14 5
      11 16 15 6
      10 9  8  7
//*****************************************************************************
#include<iostream>
using namespace std;
const int N = 30;
int arr[N][N];
int dx[N] = { 0,1,0,-1 };
int dy[N] = { 1,0,-1,0 };

int main()
{
    int n;
    cin >> n;
    int pos = 0;
    int x = 1, y = 1;
    for (int i = 1; i <= n * n; i++)
    {
        arr[x][y] = i;
        //计算接下来的位置
        int a = x + dx[pos];
        int b = y + dy[pos];
        if (a<1 || a>n || b<1 || b>n || arr[a][b])
        {
            pos = (pos + 1) % 4;//这句代码实现了方向的变换。
            a = x + dx[pos];
            b = y + dy[pos];

        }
        x = a, y = b;//更新x,y的值

    }
    for (int i = 1; i <= n; i++)
    {
        for (int j = 1; j <= n; j++)
        {
            printf("%3d", arr[i][j]);
        }
        cout << endl;
    }
    return 0;
}
