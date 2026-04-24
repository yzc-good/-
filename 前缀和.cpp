//一维前缀和---------------------------------------------------------------
#include<iostream>
#include<vector>
#include<algorithm>
using namespace std;

int main()
{
    int n = 0;
    cin >> n;
    vector<int> a(n + 1), s(n + 1, 0);
    for (int i = 1; i <= n; i++)//前缀和下标一定要从1开始。
    {
        cin >> a[i];
        s[i] = s[i - 1] + a[i];//这里就是原因，这是递推公式，构建了前缀和数组
    }
    int l, r;
    cin >> l >> r;
    cout << s[r] - s[l - 1] << endl;//这是查询公式
    return 0;
}
//****************************************************************************************
应用：最大字段和
给出一个长度为n的序列啊，选出其中连续且非空的一段使得这段和最大
例子：7
      2 -4 3 -1 2 -4 3
#include<iostream>
using namespace std;
const int N = 2e5 + 10;// 数组最大长度（20万+10，满足题目数据范围）
int n;
long long f[N];
int main()
{

    cin >> n;
    for (int i = 1; i <= n; i++)
    {
        long long x; cin >> x;
        f[i] = f[i - 1] + x;
    }
    long long ret = -1e20; // 存储最终答案（初始化为极小值，保证能被更新
    long long pervmin = 0; // 记录【i之前】最小的前缀和f[j]
    for (int i = 1; i <= n; i++)
    {// 1. 计算：以i结尾的最大子数组和 = f[i] - 前面最小的前缀和
        ret = max(ret, f[i] - pervmin);
// 2. 更新：维护到目前为止最小的前缀和
        pervmin = min(pervmin, f[i]);
    }
    cout << ret << endl;

    return 0;
}

//-------------------------------------------------------------------------
二维前缀和
//递推公式：s[i][j] = 上 + 左 - 左上 + 当前值，查询公式：sum = 大矩形 - 上 - 左 + 左上
#include <iostream>
#include <vector>
using namespace std;

int main() {
    // 1. 输入矩阵大小 n 行 m 列
    int n = 3, m = 3;
    vector<vector<int>> a(n + 1, vector<int>(m + 1)); // 原矩阵（1-based）
    vector<vector<int>> s(n + 1, vector<int>(m + 1, 0)); // 前缀和数组，初始全0

    // 2. 输入原矩阵数据
    int idx = 1;
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= m; j++) {
            a[i][j] = idx++; // 填入 1,2,3...9
        }
    }

    // 3. 构建二维前缀和数组
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= m; j++) {
            s[i][j] = s[i - 1][j] + s[i][j - 1] - s[i - 1][j - 1] + a[i][j];
        }
    }

    // 4. 查询子矩阵和：(2,2) 到 (3,3)
    int x1 = 2, y1 = 2, x2 = 3, y2 = 3;
    int sum = s[x2][y2] - s[x1 - 1][y2] - s[x2][y1 - 1] + s[x1 - 1][y1 - 1];

    cout << "子矩阵和：" << sum << endl; // 输出 28
    return 0;
}
//-------------------------------------------------------------------------
