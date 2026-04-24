std::array 是 C++11 标准库引入的静态数组容器，本质是对原生 C 风格数组的封装，既保留了原生数组 “固定大小、栈内存分配” 的特性，又补充了安全的访问方式、迭代器支持和便捷的成员函数，是替代原生数组的首选。
1. 核心特性
•	静态大小：编译期确定数组长度，大小不可动态修改（区别于 std::vector）；
•	栈内存分配：内存分配在栈上（而非堆），访问效率与原生数组一致，且无需手动释放；
•	类型安全：模板实现，明确元素类型和大小，避免原生数组的隐式类型转换问题；
•	兼容 STL：支持迭代器、size()/empty() 等 STL 容器通用接口，可直接使用 STL 算法（如 std::sort、std::find）；
•	安全访问：提供 at() 成员函数（越界抛异常），区别于原生数组的下标越界未定义行为。
•	2. 基本用法
•	（1）头文件与声明
•	使用 std::array 必须包含头文件 <array>，声明格式为：
•	cpp
•	运行
•	#include <array>  // 必须包含的头文件
•	
•	// 语法：std::array<元素类型, 数组大小> 数组名;
•	std::array<int, 5> arr;          // 声明一个int类型、长度为5的数组（默认初始化，值未定义）
•	std::array<int, 5> arr_init{1,2,3,4,5};  // C++11列表初始化（推荐）
•	std::array<int, 5> arr_default = {0};    // 部分初始化，剩余元素默认值初始化（此处为0）
•	（2）核心成员函数
函数	功能
size()	返回数组元素个数（编译期常量，效率极高）
empty()	判断数组是否为空（仅当大小为 0 时返回 true）
at(n)	访问第 n 个元素（n 从 0 开始），越界抛出 std::out_of_range 异常（安全）
operator[]	访问第 n 个元素，越界无检查（效率高，风险同原生数组）
front()	返回第一个元素的引用
back()	返回最后一个元素的引用
data()	返回指向数组首元素的原生指针（兼容 C 风格接口）
fill(val)	将数组所有元素填充为 val
swap(other)	交换两个同类型、同大小的 std::array 的内容
4. 注意事项
•	大小必须是编译期常量：std::array 的大小必须是常量表达式（如 5、const int N=10），不能用运行时变量（如 int n=5; std::array<int, n> arr; 编译报错）；
•	栈内存限制：避免声明过大的 std::array（如 std::array<int, 1000000>），栈空间不足会导致栈溢出，此时应改用 std::vector（堆内存）；
•	初始化注意：C++11 中列表初始化若元素个数少于数组大小，剩余元素会被值初始化（如 std::array<int,5>{1,2} 等价于 {1,2,0,0,0}）；
•	传参建议：传递 std::array 时建议用引用（const std::array<int,5>& arr），避免拷贝开销，同时保留大小信息。
//-----------------------------------------------------------------------------
#include <iostream>
#include <array>
#include <algorithm>
using namespace std;

bool cmp(int a,int b)
{
    if (a > b) return true;
    return false;
}
int main()
{
    array<int, 5> arr;
    for (int i = 0; i < 4; i++)
    {
        cin >> arr[i];
    }
    cout << arr.size() << endl;
    cout << arr.front() << endl;
    cout << arr.back() << endl;
    sort(arr.begin(), arr.end(),cmp);
    for (int j = 0; j < 4; j++)
    {
        cout << arr[j]<<' ';
    }
    return 0;
}
//-----------------------------------------------------------------------------
