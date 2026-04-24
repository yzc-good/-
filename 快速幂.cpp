快速幂（快速幂算法）
快速幂是高效计算幂运算的算法，核心作用：把 a^b 的计算时间从 O (b) 降到 O (logb)，算超大指数时速度极快，还能解决大数取模问题。

快速幂只做两件事：
1.	底数不断平方
2.	指数二进制位为 1 时，把当前底数乘到结果里
//----------------------------------------------------------------------------
（取模运算规则）
取模运算的规则：
当计算过程中，只有 “加法” 和 “乘法” 时，取模可以放在任意的位置
(a⋅b⋅c⋅d)%p​=(a%p⋅b%p⋅c%p⋅d%p)%p=((a⋅b%p⋅c)%p⋅d)%p
  ​
当计算过程中，存在 “减法” 时，结果是可能出现负数的，此时如果需要补正，就需要 “模加模” 的技巧来补正
(a−b)%p((a−b)%p+p)%p​
 
取模快速幂  一般题目会明确说明数据非常大，答案为对K取模后的结果。
//-----------------------------------------------------------------------------
#include<bits/stdc++.h>
using namespace std;
typedef long long LL; 
LL a,b,p;
LL qpow(LL a,LL b,LL p)
{
	LL ret=1;
	while(b)
	{
		if(b&1) ret=ret*a%p;//对P取模，防止超出范围
			a=a*a%p;//对P取模，防止超出范围
			b>>=1;
		
	}
	return ret;
}
int main()
{  
cin>>a>>b>>p;
   
cout<<a<<" "<<b<<" "<<p<<" "<<qpow(a,b,p); 

	return 0;
 }
//-----------------------------------------------------------------------------------
欧拉函数（φ(x) = 1～x 中，与 x 互质的数的个数）
如何求欧拉函数：
第一步
如果P是质数，则φ(p)=p-1

欧拉降幂：第一步：算mod的欧拉函数（φ(x) = 1～x 中，与 x 互质的数的个数）
第二步：给指数b降幂  新指数 = 原指数 mod φ(mod)
第三步：用新指数计算

例题：#include <iostream>
using namespace std;

typedef long long LL;
const LL MOD = 1000000007;
const LL PHI_MOD = MOD - 1; // 1e9+6

// 快速幂：base^exp mod modu
LL qpow(LL base, LL exp, LL modu) {
    LL ret = 1;
    base %= modu;
    while (exp > 0) {
        if (exp & 1) {
            ret = ret * base % modu;
        }
        base = base * base % modu;
        exp >>= 1;
    }
    return ret;
}

// 计算 m!     mod modu（modu=1e9+6）
//这一步就是欧拉降幂 
LL calc_fact_mod(LL m, LL modu) {
    if (m >= modu) return 0; // 阶乘包含modu因子，结果为0
    LL res = 1;
    for (LL i = 1; i <= m; ++i) {
        res = res * i % modu;
    }
    return res;
}

int main() {
    LL n, m;
    cin >> n >> m;



    // 计算指数 E = m! mod (MOD-1)
    LL E = calc_fact_mod(m, PHI_MOD);

    
  
        LL ans = qpow(n, E, MOD);
        cout << ans << endl;
    

    return 0;
}

	
