var app = angular.module('delegateApp', []);

app.controller('indexCtrl', function($scope, $http) {
    $scope.accounts = [];
    $scope.lastpayout = 0;
    $scope.nextpayout = 0;
    $scope.forged = 0;
    $scope.topay = 0;
    $scope.weight = 0;

    $http.get ('poollogs.json').then (function (res) {
        $scope.lastpayout = res.data.lastpayout * 1000;
        $scope.nextpayout = moment ($scope.lastpayout).add (1, 'week').valueOf();
        $scope.forged = res.data.forged;
        $scope.topay = res.data.topay;
        $scope.weight = res.data.weight;
        $scope.accounts = [];

        for (addr in res.data.accounts) {
            var it = res.data.accounts[addr];
            it['address'] = addr;
            $scope.accounts.push (it);
        }
    });

    $http.get ('https://wallet.shiftnrg.nl/api/delegates/get?username=seatrips').then (function (res) {
        $scope.delegate = res.data.delegate;
    });
});
