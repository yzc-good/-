以下是高精度加减乘除的模板
都是先用string 类型读入数据，再逆序存放在数组中（存放的位置公式是：a[la-1-i]=x[i]-‘0’;)


加法------------- 
#include<iostream>
#include<string>
using namespace std;
const int N = 1e6 + 10;

string x, y;
int a[N];
int b[N];
int c[N];
int lc;
void add(int c[], int a[], int b[])
{
    for (int i = 0; i < max(x.size(), y.size()); i++)
    {
        c[i] += a[i] + b[i];//对应位相加，再加上进位
        c[i + 1] += c[i] / 10;//处理进位
        c[i] = c[i] % 10;//处理余数
        
    }
    if (c[lc])// 如果 c[lc] != 0，说明最高位产生了进位
    {
        lc++;//数组长度加一
    }
}

int main()
{
   
    cin >> x >> y;
    //逆序放在数组中
    for (int i = 0; i < x.size(); i++)
    {
        a[x.size() - 1 - i] = x[i]-'0';
    }
    for (int i = 0; i < y.size(); i++)
    {
        b[y.size() - 1 - i] = y[i] - '0';
    }
    lc = max(x.size(), y.size());
    add(c, a, b);

    //输出
    for (int i = lc - 1; i >= 0; i--)
    {
        cout << c[i];
    }
    return 0;
}

减法------------------
#include<iostream>
#include<string>
using namespace std;
const int N = 1e6 + 10;
int a[N], b[N], c[N];
int la, lb, lc;

bool cmp(string& x, string& y)
{
    if (x.size() != y.size())
    {
        return x.size() < y.size();
    }
    return x < y;
}

void sub(int c[], int a[], int b[])//c=a-b
{
    for (int i = 0;i < lc; i++)
    {
        c[i] += a[i] - b[i];//对应位相减，加上借位
        if (c[i] < 0)//处理借位
        {
            c[i + 1] -= 1;//借位
            c[i] += 10;
        }
    }
    while (lc > 1 && c[lc - 1] == 0)//处理前导0
    {
        lc--;
    }
}

int main()
{
    string x, y; cin >> x >> y;
    //使x>y
    if (cmp(x, y))

    {
        swap(x, y);
        cout << '-';
    }
    la = x.size(); lb = y.size(); lc = max(la, lb);
    for (int i = 0; i < la; i++) {
        a[la - i - 1] = x[i] - '0';
    }
    for (int i = 0; i < lb; i++)
    {
        b[lb - i - 1] = y[i] - '0';
    }
    sub(c, a, b);

    for (int i = lc - 1; i >= 0; i--)
    {
        cout << c[i];
    }

    return 0;
}

乘法-------------------------
#include<iostream>
#include<string>
using namespace std;

const int N = 1e6 + 10;
int a[N], b[N], c[N];
int la, lb, lc;
 
void mul(int c[], int a[], int b[])
{
    //无进位相乘，再相加
    for (int i = 0; i < la; i++)
    {
        for (int j = 0; j < lb; j++)
        {
            c[i + j] += a[i] * b[j];
        }
    }
    //然后对c数组处理进位
    for (int i = 0; i < lc; i++)
    {
        c[i + 1] += c[i] / 10;
        c[i] %= 10;
    }
    //处理前导0
    while (lc > 1 && c[lc - 1] == 0)
    {
        lc--;
    }
}

int main()
{
    string x, y; cin >> x >> y;
   
   
    la = x.size(); lb = y.size(); lc =la+lb;
    for (int i = 0; i < la; i++) {
        a[la - i - 1] = x[i] - '0';
    }
    for (int i = 0; i < lb; i++)
    {
        b[lb - i - 1] = y[i] - '0';
    }

    mul(c, a, b);

    for (int i = lc - 1; i >= 0; i--)
    {
        cout << c[i];
    }
    return 0;
}

除法--------------------------

#include<iostream>
#include<string>
using namespace std;

const int N = 1e6 + 10;
int a[N], b, c[N];
typedef long long ll;
int la, lc;

void sub(int c[], int a[], int b)
{
    ll t = 0;//标记每次除完的余数
    for (int i = la - 1; i >= 0; i--)
    {
        //计算当前的被除数
        t = t * 10 + a[i];
        c[i] = t / b;//商
        t %= b;//余数
    }

    //处理前导0
    while (lc > 1 && c[lc - 1] == 0)
    {
        lc--;
    }
}

int main()
{
    string x; cin >> x >> b;
    la = x.size();

    for (int i = 0; i < la; i++)
    {
        a[la - 1 - i] = x[i] - '0';
    }

    lc = la;

    sub(c, a, b);
    for (int i = lc - 1; i >= 0; i--)
    {
        cout << c[i];
    }
    return 0;
}
