//二分查找的左端点
int l = 1, r = n;
while (l < r)
{
    int mid = (l + r) / 2;
    if (check(mid)) r = mid;
    else l = mid + 1;
}
//二分查找的右段点
int l=1,r=n;
while(l<r)
{
int mid=(l+r+1)/2;
if(check(mid)) l=mid;
else r=mid-1;
}
//标黄的代码需要分析出来，可以用1 1 2 2 2 3 4 5来帮助分析
//为了防止溢出，求中点时可以用下面方式
//mid = l + (r - l) / 2;
//**************************************************************************************
//2026/03/25--------------------------------------------------------------
//我今天接触到了用二分来求N次方根
#include<iostream>
#include<iomanip>
using namespace std;

const double eps = 1e-12;

int main()
{
    long long N, M;
    cin >> N >> M;

    double l = 0, r = 100000, res = 0;

    while (r - l > eps)  // 浮点数二分标准写法
    {
        double mid = (l + r) / 2;

        // 每次都重新计算 mid^M，必须重置为 1
        double pow_result = 1.0;
        for (int i = 0; i < M; i++) {
            pow_result *= mid;
        }

        if (pow_result >= N) {
            r = mid;
        }
        else {
            l = mid;
            res = mid;
        }
    }

    cout << fixed << setprecision(7) << res << endl;
    return 0;
}
